"""Build the themen.apkg deck from themen/*.md.

Each markdown file becomes its own subdeck under "German::Themen::<title>".
Each sentence produces TWO cards:
  - EN -> DE production (front English; back German + audio + context)
  - DE -> EN comprehension (front German + audio; back English + context)

Usage:
    python anki/build_themen.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import genanki

sys.path.insert(0, str(Path(__file__).parent))

from build import CARD_CSS, PROD_MODEL, parse_topic, strip_cloze, stable_guid
from tts import synth, DEFAULT_VOICE

ROOT = Path(__file__).parent.parent
THEMEN_DIR = ROOT / "themen"
OUT_DIR = ROOT / "anki" / "out"

DE_TO_EN_MODEL_ID = 1607392330


DE_TO_EN_MODEL = genanki.Model(
    DE_TO_EN_MODEL_ID,
    "German DE->EN Comprehension",
    fields=[
        {"name": "German"},
        {"name": "English"},
        {"name": "Audio"},
        {"name": "Context"},
    ],
    templates=[
        {
            "name": "DE -> EN",
            "qfmt": '<div class="de">{{German}}</div><div>{{Audio}}</div>',
            "afmt": (
                '<div class="de">{{German}}</div>'
                '<div>{{Audio}}</div>'
                "<hr>"
                '<div class="en">{{English}}</div>'
                '<div class="grammar">{{Context}}</div>'
            ),
        }
    ],
    css=CARD_CSS,
)


def deck_id_for(topic_id: str) -> int:
    """Stable per-topic deck id derived from the topic_id."""
    digest = hashlib.sha1(topic_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % (2 ** 31)


def main():
    if not THEMEN_DIR.is_dir():
        raise SystemExit(f"Missing {THEMEN_DIR}")

    files = sorted(THEMEN_DIR.glob("*.md"))
    if not files:
        raise SystemExit(f"No .md files in {THEMEN_DIR}")

    decks: list[genanki.Deck] = []
    media: list[str] = []
    total_sentences = 0

    for mf in files:
        topic = parse_topic(mf)
        print(f"  {mf.name}  ({len(topic.sentences)} sentences)")
        total_sentences += len(topic.sentences)

        deck = genanki.Deck(
            deck_id_for(topic.topic_id),
            f"German::Themen::{topic.title}",
        )

        for idx, (de_raw, en) in enumerate(topic.sentences):
            de = strip_cloze(de_raw)
            audio_path = synth(de, voice=DEFAULT_VOICE)
            media.append(str(audio_path))
            audio_tag = f"[sound:{audio_path.name}]"
            tags = [topic.level, topic.topic_id] + topic.tags

            deck.add_note(genanki.Note(
                model=PROD_MODEL,
                fields=[en, de, audio_tag, topic.grammar_html],
                tags=tags,
                guid=stable_guid(topic.topic_id, str(idx), "prod"),
            ))
            deck.add_note(genanki.Note(
                model=DE_TO_EN_MODEL,
                fields=[de, en, audio_tag, topic.grammar_html],
                tags=tags,
                guid=stable_guid(topic.topic_id, str(idx), "de2en"),
            ))

        decks.append(deck)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "themen.apkg"
    genanki.Package(decks, media_files=media).write_to_file(str(out))
    print(f"Wrote {out}")
    print(f"Total: {total_sentences} sentences across {len(decks)} subdecks")


if __name__ == "__main__":
    main()
