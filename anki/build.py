"""Build .apkg decks from grammar/<level>/*.md.

Each markdown file produces three cards per sentence in the "## Sätze" section:
  - cloze (German with blank, audio on front + back)
  - EN -> DE production (English on front, German + audio on back)
  - listening (audio-only on front, German + English on back)

The "## Erklärung" section appears on the back of every card from that file.

Usage:
    python anki/build.py --level A1
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import genanki
import markdown as md
import yaml

from tts import synth, DEFAULT_VOICE

ROOT = Path(__file__).parent.parent
GRAMMAR_DIR = ROOT / "grammar"
OUT_DIR = ROOT / "anki" / "out"

# Stable model IDs (random ints, do NOT change after publishing).
CLOZE_MODEL_ID = 1607392319
PROD_MODEL_ID = 1607392320
LISTEN_MODEL_ID = 1607392321

# Stable per-level deck IDs.
DECK_IDS = {"A1": 2059400110, "A2": 2059400111, "B1": 2059400112, "B2": 2059400113}

CARD_CSS = """
.card { font-family: -apple-system, system-ui, sans-serif; font-size: 22px; color: #222; background: #fafafa; text-align: center; padding: 24px; }
.de { font-size: 26px; }
.en { color: #555; font-style: italic; margin-top: 8px; }
.grammar { text-align: left; margin-top: 18px; padding: 12px 14px; background: #fff; border-left: 3px solid #b3d4fc; font-size: 16px; color: #333; }
.grammar h2, .grammar h3 { font-size: 16px; margin: 4px 0; }
.grammar table { border-collapse: collapse; margin: 6px 0; }
.grammar td, .grammar th { border: 1px solid #ccc; padding: 3px 8px; }
.cloze { font-weight: bold; color: #2563eb; }
.hint { color: #888; font-size: 14px; margin-top: 10px; font-style: italic; }
hr { border: none; border-top: 1px solid #ddd; margin: 14px 0; }
"""

CLOZE_MODEL = genanki.Model(
    CLOZE_MODEL_ID,
    "German Cloze (with audio)",
    fields=[
        {"name": "Text"},
        {"name": "English"},
        {"name": "Audio"},
        {"name": "Grammar"},
    ],
    templates=[
        {
            "name": "Cloze",
            "qfmt": '<div class="de">{{cloze:Text}}</div><div>{{Audio}}</div>',
            "afmt": (
                '<div class="de">{{cloze:Text}}</div>'
                '<div>{{Audio}}</div>'
                '<div class="en">{{English}}</div>'
                "<hr>"
                '<div class="grammar">{{Grammar}}</div>'
            ),
        }
    ],
    css=CARD_CSS,
    model_type=genanki.Model.CLOZE,
)

PROD_MODEL = genanki.Model(
    PROD_MODEL_ID,
    "German EN->DE Production",
    fields=[
        {"name": "English"},
        {"name": "German"},
        {"name": "Audio"},
        {"name": "Grammar"},
    ],
    templates=[
        {
            "name": "EN -> DE",
            "qfmt": '<div class="en">{{English}}</div>',
            "afmt": (
                '<div class="en">{{English}}</div>'
                "<hr>"
                '<div class="de">{{German}}</div>'
                '<div>{{Audio}}</div>'
                '<div class="grammar">{{Grammar}}</div>'
            ),
        }
    ],
    css=CARD_CSS,
)

LISTEN_MODEL = genanki.Model(
    LISTEN_MODEL_ID,
    "German Listening (audio-only front)",
    fields=[
        {"name": "Audio"},
        {"name": "German"},
        {"name": "English"},
        {"name": "Grammar"},
    ],
    templates=[
        {
            "name": "Listen",
            "qfmt": '<div>{{Audio}}</div><div class="hint">Hör zu und übersetze</div>',
            "afmt": (
                '<div>{{Audio}}</div>'
                "<hr>"
                '<div class="de">{{German}}</div>'
                '<div class="en">{{English}}</div>'
                '<div class="grammar">{{Grammar}}</div>'
            ),
        }
    ],
    css=CARD_CSS,
)


@dataclass
class Topic:
    path: Path
    title: str
    level: str
    topic_id: str
    tags: list[str]
    grammar_html: str
    sentences: list[tuple[str, str]]  # (german_with_cloze, english)


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
SENTENCE_RE = re.compile(r"^\s*-\s*(.+?)\s*\|\s*(.+?)\s*$")
CLOZE_RE = re.compile(r"\{\{c\d+::(.+?)(?:::.+?)?\}\}")


def parse_topic(path: Path) -> Topic:
    raw = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)

    sections: dict[str, list[str]] = {}
    current = None
    for line in body.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            current = h.group(1).strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)

    erklaerung_md = "\n".join(sections.get("Erklärung", [])).strip()
    grammar_html = md.markdown(erklaerung_md, extensions=["tables"]) if erklaerung_md else ""

    sentences: list[tuple[str, str]] = []
    for line in sections.get("Sätze", []):
        sm = SENTENCE_RE.match(line)
        if sm:
            sentences.append((sm.group(1).strip(), sm.group(2).strip()))

    return Topic(
        path=path,
        title=str(meta.get("title", path.stem)),
        level=str(meta.get("level", "A1")),
        topic_id=str(meta.get("topic_id", path.stem)),
        tags=list(meta.get("tags", [])),
        grammar_html=grammar_html,
        sentences=sentences,
    )


def strip_cloze(text: str) -> str:
    """Remove cloze markup, keeping the inner answer."""
    return CLOZE_RE.sub(lambda m: m.group(1), text)


def stable_guid(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def deck_id_for_topic(topic_id: str) -> int:
    """Stable per-topic deck id derived from topic_id."""
    digest = hashlib.sha1(topic_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % (2 ** 31)


FILE_PREFIX_RE = re.compile(r"^(\d+)-")


def build_level(level: str) -> Path:
    src_dir = GRAMMAR_DIR / level
    if not src_dir.is_dir():
        raise SystemExit(f"No grammar/{level}/ directory found")

    topic_files = sorted(src_dir.glob("*.md"))
    if not topic_files:
        raise SystemExit(f"No .md files in {src_dir}")

    decks: list[genanki.Deck] = []
    media: list[str] = []

    for tf in topic_files:
        topic = parse_topic(tf)
        print(f"  {tf.name}  ({len(topic.sentences)} sentences)")

        # Use the file's leading number to keep subdecks in pedagogical order
        # (Anki sorts subdecks alphabetically).
        prefix_match = FILE_PREFIX_RE.match(tf.name)
        prefix = prefix_match.group(1) + " " if prefix_match else ""
        deck_name = f"German::{level}::{prefix}{topic.title}"

        deck = genanki.Deck(deck_id_for_topic(topic.topic_id), deck_name)

        for idx, (de_clozed, en) in enumerate(topic.sentences):
            de_plain = strip_cloze(de_clozed)
            audio_path = synth(de_plain, voice=DEFAULT_VOICE)
            media.append(str(audio_path))
            audio_tag = f"[sound:{audio_path.name}]"
            tags = [topic.level, topic.topic_id] + topic.tags

            deck.add_note(genanki.Note(
                model=CLOZE_MODEL,
                fields=[de_clozed, en, audio_tag, topic.grammar_html],
                tags=tags,
                guid=stable_guid(topic.topic_id, str(idx), "cloze"),
            ))
            deck.add_note(genanki.Note(
                model=PROD_MODEL,
                fields=[en, de_plain, audio_tag, topic.grammar_html],
                tags=tags,
                guid=stable_guid(topic.topic_id, str(idx), "prod"),
            ))
            deck.add_note(genanki.Note(
                model=LISTEN_MODEL,
                fields=[audio_tag, de_plain, en, topic.grammar_html],
                tags=tags,
                guid=stable_guid(topic.topic_id, str(idx), "listen"),
            ))

        decks.append(deck)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{level}.apkg"
    genanki.Package(decks, media_files=media).write_to_file(str(out))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True, choices=list(DECK_IDS))
    args = ap.parse_args()
    print(f"Building German::{args.level}...")
    out = build_level(args.level)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
