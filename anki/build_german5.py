"""Build the German 5 (A2.2-B1.1) verb deck from german5/*.md.

Source is a markdown table with one row per verb:
    | Infinitiv | Präsens (er) | Präteritum | Perfekt | English | Beispiel | Beispiel EN | Tags |

Each verb produces up to four cards:
  1. DE -> EN      infinitive + audio  ->  English
  2. EN -> DE      English             ->  infinitive + audio
  3. Stammformen   infinitive          ->  Präsens / Präteritum / Perfekt + example sentence
  4. Präsens-Drill infinitive          ->  er/sie/es form   (only for stem-changing verbs,
                                           i.e. rows tagged `stammwechsel`)

Usage:
    python anki/build_german5.py
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
SRC_DIR = ROOT / "german5"
OUT_DIR = ROOT / "anki" / "out"

MODEL_ID = 1607392340
DECK_ID = 2059400130
DECK_NAME = "German5::100 Verben"

CARD_CSS = """
.card { font-family: -apple-system, system-ui, sans-serif; font-size: 22px; color: #222; background: #fafafa; text-align: center; padding: 24px; }
.inf { font-size: 30px; font-weight: 600; }
.en { color: #555; font-style: italic; font-size: 22px; }
.ask { color: #888; font-size: 15px; margin-top: 12px; letter-spacing: .04em; text-transform: uppercase; }
table.forms { margin: 14px auto; border-collapse: collapse; font-size: 20px; }
table.forms td { padding: 4px 10px; border-bottom: 1px solid #e4e4e4; }
table.forms td.label { color: #888; font-size: 14px; text-align: right; text-transform: uppercase; letter-spacing: .04em; }
table.forms td.form { text-align: left; font-weight: 600; }
.praet { color: #b45309; }
.perf { color: #2563eb; }
.beispiel { margin-top: 16px; padding: 12px 14px; background: #fff; border-left: 3px solid #b3d4fc; text-align: left; font-size: 19px; }
.beispiel .en { font-size: 16px; }
.tags { color: #aaa; font-size: 13px; margin-top: 14px; }
hr { border: none; border-top: 1px solid #ddd; margin: 14px 0; }
"""

FORMS_TABLE = """
<table class="forms">
  <tr><td class="label">Präsens</td><td class="form">er/sie/es {{Praesens}}</td></tr>
  <tr><td class="label">Präteritum</td><td class="form praet">{{Praeteritum}}</td></tr>
  <tr><td class="label">Perfekt</td><td class="form perf">{{Perfekt}}</td></tr>
</table>
<div>{{AudioFormen}}</div>
"""

BEISPIEL = """
<div class="beispiel">{{Beispiel}}<div>{{AudioBeispiel}}</div><div class="en">{{BeispielEN}}</div></div>
"""

MODEL = genanki.Model(
    MODEL_ID,
    "German5 Verb (Stammformen)",
    fields=[
        {"name": "Infinitiv"},
        {"name": "Praesens"},
        {"name": "Praeteritum"},
        {"name": "Perfekt"},
        {"name": "English"},
        {"name": "Beispiel"},
        {"name": "BeispielEN"},
        {"name": "AudioInfinitiv"},
        {"name": "AudioFormen"},
        {"name": "AudioBeispiel"},
        {"name": "Stammwechsel"},
        {"name": "Typ"},
    ],
    templates=[
        {
            "name": "1 DE -> EN",
            "qfmt": '<div class="inf">{{Infinitiv}}</div><div>{{AudioInfinitiv}}</div>',
            "afmt": (
                '<div class="inf">{{Infinitiv}}</div><div>{{AudioInfinitiv}}</div><hr>'
                '<div class="en">{{English}}</div>' + FORMS_TABLE
            ),
        },
        {
            "name": "2 EN -> DE",
            "qfmt": '<div class="en">{{English}}</div><div class="ask">Infinitiv?</div>',
            "afmt": (
                '<div class="en">{{English}}</div><hr>'
                '<div class="inf">{{Infinitiv}}</div><div>{{AudioInfinitiv}}</div>'
                + FORMS_TABLE
            ),
        },
        {
            "name": "3 Stammformen",
            "qfmt": (
                '<div class="inf">{{Infinitiv}}</div>'
                '<div class="ask">Präsens &middot; Präteritum &middot; Perfekt?</div>'
            ),
            "afmt": (
                '<div class="inf">{{Infinitiv}}</div>'
                '<div class="en">{{English}}</div>' + FORMS_TABLE + BEISPIEL
                + '<div class="tags">{{Typ}}</div>'
            ),
        },
        {
            "name": "4 Präsens-Drill",
            "qfmt": (
                "{{#Stammwechsel}}"
                '<div class="inf">{{Infinitiv}}</div>'
                '<div class="ask">er / sie / es &hellip;?</div>'
                "{{/Stammwechsel}}"
            ),
            "afmt": (
                '<div class="inf">{{Infinitiv}}</div><hr>'
                '<div class="inf">er/sie/es {{Praesens}}</div>'
                '<div class="en">{{English}}</div>' + FORMS_TABLE
            ),
        },
    ],
    css=CARD_CSS,
)


@dataclass
class Verb:
    infinitiv: str
    praesens: str
    praeteritum: str
    perfekt: str
    english: str
    beispiel: str
    beispiel_en: str
    tags: list[str]


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")


def parse_verbs(path: Path) -> tuple[dict, list[Verb]]:
    raw = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(m.group(1)) or {}

    verbs: list[Verb] = []
    for line in m.group(2).splitlines():
        line = line.strip()
        if not line.startswith("|") or SEPARATOR_RE.match(line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0] == "Infinitiv":  # header
            continue
        if len(cells) != 8:
            raise ValueError(f"{path}: expected 8 columns, got {len(cells)}: {line}")
        verbs.append(Verb(*cells[:7], tags=cells[7].split()))
    return meta, verbs


def tts_text(form: str) -> str:
    """Drop the parenthetical note so the TTS reads only the form itself."""
    return form.split(" (")[0].strip()


def stable_guid(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def build() -> Path:
    src_files = sorted(SRC_DIR.glob("*.md"))
    if not src_files:
        raise SystemExit(f"No .md files in {SRC_DIR}")

    deck = genanki.Deck(DECK_ID, DECK_NAME)
    media: list[str] = []
    seen: set[str] = set()
    cards = 0

    for sf in src_files:
        meta, verbs = parse_verbs(sf)
        print(f"  {sf.name}  ({len(verbs)} verbs)")
        for v in verbs:
            if v.infinitiv in seen:
                raise SystemExit(f"Duplicate verb: {v.infinitiv}")
            seen.add(v.infinitiv)

            chain = f"{v.infinitiv}, er {v.praesens}, {tts_text(v.praeteritum)}, {tts_text(v.perfekt)}"
            clips = [synth(t, voice=DEFAULT_VOICE) for t in (v.infinitiv, chain, v.beispiel)]
            media.extend(str(c) for c in clips)
            a_inf, a_formen, a_bsp = (f"[sound:{c.name}]" for c in clips)

            stammwechsel = "1" if "stammwechsel" in v.tags else ""
            deck.add_note(genanki.Note(
                model=MODEL,
                fields=[
                    v.infinitiv, v.praesens, v.praeteritum, v.perfekt, v.english,
                    v.beispiel, v.beispiel_en, a_inf, a_formen, a_bsp,
                    stammwechsel, " &middot; ".join(v.tags),
                ],
                tags=["german5", "verbentest"] + v.tags,
                guid=stable_guid("german5", v.infinitiv),
            ))
            cards += 4 if stammwechsel else 3

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "German5-100Verben.apkg"
    genanki.Package([deck], media_files=media).write_to_file(str(out))
    print(f"  {len(seen)} verbs -> {cards} cards")
    return out


if __name__ == "__main__":
    print(f"Building {DECK_NAME}...")
    print(f"Wrote {build()}")
