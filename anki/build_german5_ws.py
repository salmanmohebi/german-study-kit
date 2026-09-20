"""Build the German 5 vocabulary decks from german5/ws/*.md.

One markdown file per printed word list in the course Materialsammlung; each
file's frontmatter names its Anki deck, the source pages, the Quizlet set the
handout links to, and the card type:

  vocab   -> two cards: DE -> EN and EN -> DE
  phrase  -> one card:  EN -> DE (producing the phrase is the point)
  cloze   -> one cloze card, for gap-fill material (adjective endings,
             connectors, prepositions, verb + preposition)

Usage:
    python anki/build_german5_ws.py
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import genanki
import yaml

from tts import synth, DEFAULT_VOICE

ROOT = Path(__file__).parent.parent
SRC_DIR = ROOT / "german5" / "ws"
OUT_DIR = ROOT / "anki" / "out"

WORT_MODEL_ID = 1607392350
CLOZE_MODEL_ID = 1607392351

CARD_CSS = """
.card { font-family: -apple-system, system-ui, sans-serif; font-size: 22px; color: #222; background: #fafafa; text-align: center; padding: 24px; }
.de { font-size: 26px; line-height: 1.45; }
.en { color: #555; font-style: italic; font-size: 20px; margin-top: 8px; }
.ask { color: #888; font-size: 14px; margin-top: 12px; letter-spacing: .04em; text-transform: uppercase; }
.extra { margin-top: 16px; padding: 10px 14px; background: #fff; border-left: 3px solid #b3d4fc; text-align: left; font-size: 18px; }
.src { color: #bbb; font-size: 12px; margin-top: 16px; }
.cloze { font-weight: bold; color: #2563eb; }
hr { border: none; border-top: 1px solid #ddd; margin: 14px 0; }
"""

EXTRA = '{{#Extra}}<div class="extra">{{Extra}}</div>{{/Extra}}'
SRC = '<div class="src">{{Quelle}}</div>'

WORT_MODEL = genanki.Model(
    WORT_MODEL_ID,
    "German5 Wortschatz",
    fields=[
        {"name": "German"}, {"name": "English"}, {"name": "Extra"},
        {"name": "Audio"}, {"name": "Quelle"},
        {"name": "Erkennen"}, {"name": "Produzieren"},
    ],
    templates=[
        {
            "name": "1 DE -> EN",
            "qfmt": "{{#Erkennen}}" '<div class="de">{{German}}</div><div>{{Audio}}</div>' "{{/Erkennen}}",
            "afmt": ('<div class="de">{{German}}</div><div>{{Audio}}</div><hr>'
                     '<div class="en">{{English}}</div>' + EXTRA + SRC),
        },
        {
            "name": "2 EN -> DE",
            "qfmt": "{{#Produzieren}}" '<div class="en">{{English}}</div>'
                    '<div class="ask">Auf Deutsch?</div>' "{{/Produzieren}}",
            "afmt": ('<div class="en">{{English}}</div><hr>'
                     '<div class="de">{{German}}</div><div>{{Audio}}</div>' + EXTRA + SRC),
        },
    ],
    css=CARD_CSS,
)

CLOZE_MODEL = genanki.Model(
    CLOZE_MODEL_ID,
    "German5 Cloze",
    fields=[
        {"name": "Text"}, {"name": "English"}, {"name": "Extra"},
        {"name": "Audio"}, {"name": "Quelle"},
    ],
    templates=[
        {
            "name": "Cloze",
            "qfmt": '<div class="de">{{cloze:Text}}</div><div class="en">{{English}}</div>',
            "afmt": ('<div class="de">{{cloze:Text}}</div><div>{{Audio}}</div>'
                     '<div class="en">{{English}}</div>' + EXTRA + SRC),
        }
    ],
    css=CARD_CSS,
    model_type=genanki.Model.CLOZE,
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")
CLOZE_RE = re.compile(r"\{\{c\d+::(.+?)(?:::.+?)?\}\}")
TYPES = {"vocab", "phrase", "cloze"}


@dataclass
class WordList:
    meta: dict
    rows: list[tuple[str, str, str]]


def parse_list(path: Path) -> WordList:
    raw = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(m.group(1)) or {}
    for key in ("title", "deck", "type", "pages"):
        if key not in meta:
            raise ValueError(f"{path}: frontmatter missing '{key}'")
    if meta["type"] not in TYPES:
        raise ValueError(f"{path}: unknown type {meta['type']!r}")

    rows: list[tuple[str, str, str]] = []
    for line in m.group(2).splitlines():
        line = line.strip()
        if not line.startswith("|") or SEPARATOR_RE.match(line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0] in ("German", "Text"):
            continue
        if len(cells) != 3:
            raise ValueError(f"{path}: expected 3 columns, got {len(cells)}: {line}")
        if meta["type"] == "cloze" and not CLOZE_RE.search(cells[0]):
            raise ValueError(f"{path}: no cloze in: {line}")
        rows.append(tuple(cells))
    if not rows:
        raise ValueError(f"{path}: no rows")
    return WordList(meta, rows)


def strip_cloze(text: str) -> str:
    return CLOZE_RE.sub(lambda m: m.group(1), text)


def stable_guid(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def deck_id_for(name: str) -> int:
    return int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16) % (2 ** 31)


def build() -> Path:
    files = sorted(SRC_DIR.glob("*.md"))
    if not files:
        raise SystemExit(f"No .md files in {SRC_DIR}")

    decks: list[genanki.Deck] = []
    media: list[str] = []
    total = 0

    for f in files:
        wl = parse_list(f)
        meta, typ = wl.meta, wl.meta["type"]
        deck = genanki.Deck(deck_id_for(meta["deck"]), meta["deck"])
        quelle = f"S. {meta['pages']}"
        if meta.get("quizlet"):
            quelle += f" &middot; {meta['quizlet']}"
        tags = ["german5", f"L{int(meta['lesson']):02d}", meta.get("tag", f.stem)]

        seen: set[str] = set()
        for idx, (german, english, extra) in enumerate(wl.rows):
            plain = strip_cloze(german)
            if plain.lower() in seen:
                raise SystemExit(f"{f.name}: duplicate entry {plain!r}")
            seen.add(plain.lower())

            audio_path = synth(re.sub(r"\s*\([^)]*\)", "", plain).strip() or plain,
                               voice=DEFAULT_VOICE)
            media.append(str(audio_path))
            audio = f"[sound:{audio_path.name}]"

            if typ == "cloze":
                note = genanki.Note(
                    model=CLOZE_MODEL,
                    fields=[german, english, extra, audio, quelle],
                    tags=tags, guid=stable_guid("g5ws", meta["deck"], str(idx)),
                )
                total += 1
            else:
                note = genanki.Note(
                    model=WORT_MODEL,
                    fields=[german, english, extra, audio, quelle,
                            "1" if typ == "vocab" else "", "1"],
                    tags=tags, guid=stable_guid("g5ws", meta["deck"], str(idx)),
                )
                total += 2 if typ == "vocab" else 1
            deck.add_note(note)

        print(f"  {f.name:44} {len(wl.rows):4} entries  {typ:6}  -> {meta['deck']}")
        decks.append(deck)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "German5-Wortschatz.apkg"
    genanki.Package(decks, media_files=media).write_to_file(str(out))
    print(f"  {len(decks)} decks, {total} cards")
    return out


if __name__ == "__main__":
    print("Building German5 Wortschatz decks...")
    print(f"Wrote {build()}")
