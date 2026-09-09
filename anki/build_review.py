"""Build cumulative review decks from review/<level>/*.md.

Unlike build.py (three cards per sentence), each sentence here produces exactly
ONE card: a gap-fill with English context on the front, and on the back the full
sentence, audio, and a per-card grammar tip written for that specific sentence.

Sentence line format (three pipe-separated fields):
    - Ich {{c1::bin}} müde. | I am tired. | sein: ich -> bin. Always irregular.

Usage:
    python anki/build_review.py --level A1
"""
from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import genanki
import markdown as md
import yaml

from tts import synth, DEFAULT_VOICE

ROOT = Path(__file__).parent.parent
SRC_DIR = ROOT / "review"
OUT_DIR = ROOT / "anki" / "out"

# Stable model / deck IDs (random ints, do NOT change after publishing).
REVIEW_MODEL_ID = 1607392330
DECK_IDS = {"A1": 2059400120, "A2": 2059400121}

CARD_CSS = """
.card { font-family: -apple-system, system-ui, sans-serif; font-size: 22px; color: #222; background: #fafafa; text-align: center; padding: 24px; }
.de { font-size: 26px; line-height: 1.5; }
.en { color: #555; font-style: italic; margin-top: 10px; font-size: 19px; }
.tip { text-align: left; margin-top: 18px; padding: 12px 14px; background: #fffbe6; border-left: 3px solid #f0c000; font-size: 17px; color: #333; }
.topic { color: #888; font-size: 14px; letter-spacing: .04em; text-transform: uppercase; margin-bottom: 14px; }
.cloze { font-weight: bold; color: #2563eb; }
hr { border: none; border-top: 1px solid #ddd; margin: 14px 0; }
"""

REVIEW_MODEL = genanki.Model(
    REVIEW_MODEL_ID,
    "German Review (gap-fill + grammar tip)",
    fields=[
        {"name": "Text"},
        {"name": "English"},
        {"name": "Audio"},
        {"name": "Tip"},
        {"name": "Topic"},
    ],
    templates=[
        {
            "name": "Review",
            "qfmt": (
                '<div class="topic">{{Topic}}</div>'
                '<div class="de">{{cloze:Text}}</div>'
                '<div class="en">{{English}}</div>'
            ),
            "afmt": (
                '<div class="topic">{{Topic}}</div>'
                '<div class="de">{{cloze:Text}}</div>'
                '<div>{{Audio}}</div>'
                '<div class="en">{{English}}</div>'
                "<hr>"
                '<div class="tip">{{Tip}}</div>'
            ),
        }
    ],
    css=CARD_CSS,
    model_type=genanki.Model.CLOZE,
)


@dataclass
class Topic:
    title: str
    level: str
    topic_id: str
    tags: list[str]
    sentences: list[tuple[str, str, str]]  # (german_with_cloze, english, tip)


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
CLOZE_RE = re.compile(r"\{\{c\d+::(.+?)(?:::.+?)?\}\}")
FILE_PREFIX_RE = re.compile(r"^(\d+)-")


def parse_topic(path: Path) -> Topic:
    raw = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(m.group(1)) or {}

    sentences: list[tuple[str, str, str]] = []
    for line in m.group(2).splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) != 3:
            raise ValueError(f"{path}: expected 3 fields, got {len(parts)}: {line}")
        de, en, tip = parts
        if not CLOZE_RE.search(de):
            raise ValueError(f"{path}: no cloze in: {line}")
        sentences.append((de, en, md.markdown(tip)))

    return Topic(
        title=str(meta.get("title", path.stem)),
        level=str(meta.get("level", "A1")),
        topic_id=str(meta.get("topic_id", path.stem)),
        tags=list(meta.get("tags", [])),
        sentences=sentences,
    )


def strip_cloze(text: str) -> str:
    return CLOZE_RE.sub(lambda m: m.group(1), text)


def stable_guid(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def build_level(level: str) -> Path:
    src = SRC_DIR / level
    if not src.is_dir():
        raise SystemExit(f"No review/{level}/ directory found")
    topic_files = sorted(src.glob("*.md"))
    if not topic_files:
        raise SystemExit(f"No .md files in {src}")

    deck = genanki.Deck(DECK_IDS[level], f"German::{level} Review")
    media: list[str] = []
    seen: dict[str, str] = {}
    total = 0

    for tf in topic_files:
        topic = parse_topic(tf)
        prefix_match = FILE_PREFIX_RE.match(tf.name)
        label = (prefix_match.group(1) + ". " if prefix_match else "") + topic.title
        print(f"  {tf.name}  ({len(topic.sentences)} cards)")

        for idx, (de_clozed, en, tip) in enumerate(topic.sentences):
            de_plain = strip_cloze(de_clozed)
            key = de_plain.lower()
            if key in seen:
                raise SystemExit(f"Duplicate sentence in {tf.name} (also {seen[key]}): {de_plain}")
            seen[key] = tf.name

            audio_path = synth(de_plain, voice=DEFAULT_VOICE)
            media.append(str(audio_path))
            deck.add_note(genanki.Note(
                model=REVIEW_MODEL,
                fields=[de_clozed, en, f"[sound:{audio_path.name}]", tip, label],
                tags=[f"{level}-review", topic.topic_id] + topic.tags,
                guid=stable_guid("review", topic.topic_id, str(idx)),
            ))
            total += 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{level}-review.apkg"
    genanki.Package([deck], media_files=media).write_to_file(str(out))
    print(f"  total: {total} cards")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True, choices=list(DECK_IDS))
    args = ap.parse_args()
    print(f"Building German::{args.level} Review...")
    print(f"Wrote {build_level(args.level)}")


if __name__ == "__main__":
    main()
