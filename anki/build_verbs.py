"""Build the irregular-verbs Anki deck from reference/irregular-verbs.md.

Each verb in the markdown table becomes one card:
  Front: infinitive + audio + meaning
  Back: Präteritum + Partizip II (with helper) + audio of all three forms

Usage:
    python anki/build_verbs.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import genanki

sys.path.insert(0, str(Path(__file__).parent))

from build import CARD_CSS, stable_guid
from tts import synth, DEFAULT_VOICE

ROOT = Path(__file__).parent.parent
SOURCE = ROOT / "reference" / "irregular-verbs.md"
OUT_DIR = ROOT / "anki" / "out"

VERB_DECK_ID = 2059400120
VERB_MODEL_ID = 1607392325


VERB_MODEL = genanki.Model(
    VERB_MODEL_ID,
    "German Irregular Verb",
    fields=[
        {"name": "Infinitiv"},
        {"name": "Praeteritum"},
        {"name": "PartizipII"},
        {"name": "Helper"},
        {"name": "Meaning"},
        {"name": "AudioInf"},
        {"name": "AudioForms"},
    ],
    templates=[
        {
            "name": "Forms",
            "qfmt": (
                '<div class="de" style="font-size:32px;">{{Infinitiv}}</div>'
                '<div>{{AudioInf}}</div>'
                '<div class="en" style="margin-top:10px;">{{Meaning}}</div>'
            ),
            "afmt": (
                '<div class="de" style="font-size:24px;">{{Infinitiv}}</div>'
                "<hr>"
                '<table style="margin: 12px auto; border-collapse: collapse; font-size: 20px;">'
                '<tr><td style="padding: 6px 14px; text-align: right; color: #666;">Präteritum:</td>'
                '<td style="padding: 6px 14px;"><b>{{Praeteritum}}</b></td></tr>'
                '<tr><td style="padding: 6px 14px; text-align: right; color: #666;">Partizip II:</td>'
                '<td style="padding: 6px 14px;"><b>{{Helper}} {{PartizipII}}</b></td></tr>'
                "</table>"
                '<div>{{AudioForms}}</div>'
                '<div class="en" style="margin-top: 10px;">{{Meaning}}</div>'
            ),
        }
    ],
    css=CARD_CSS,
)


SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")


def parse_verbs(text: str):
    """Yield dicts for each verb row in the markdown tables."""
    current_section = None
    for line in text.splitlines():
        stripped = line.strip()
        m = SECTION_RE.match(stripped)
        if m:
            current_section = m.group(1).strip()
            continue
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cols = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cols) != 5:
            continue
        # Skip header
        if cols[0].lower() == "infinitiv":
            continue
        # Skip separator rows like |---|---|...
        if all(c.startswith("--") or c == "" for c in cols):
            continue
        # Sanity: helper column must be 'haben' or 'sein'
        if cols[3].lower() not in ("haben", "sein"):
            continue
        infinitiv, praet, p2, helper, meaning = cols
        yield {
            "section": current_section,
            "infinitiv": infinitiv,
            "praeteritum": praet,
            "partizip2": p2,
            "helper": helper.lower() == "sein" and "ist" or "hat",  # display form
            "helper_raw": helper.lower(),
            "meaning": meaning,
        }


def section_to_tag(section: str | None) -> str:
    if not section:
        return "verbs::misc"
    slug = re.sub(r"[^a-z0-9]+", "-", section.lower()).strip("-")
    return f"verbs::{slug}"


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing source file: {SOURCE}")
    text = SOURCE.read_text(encoding="utf-8")
    verbs = list(parse_verbs(text))
    if not verbs:
        raise SystemExit("No verbs parsed — check markdown table format")

    print(f"Building German::Verbs::Unregelmäßig from {len(verbs)} verbs...")

    deck = genanki.Deck(VERB_DECK_ID, "German::Verbs::Unregelmäßig")
    media: list[str] = []

    for v in verbs:
        audio_inf = synth(v["infinitiv"], voice=DEFAULT_VOICE)
        forms_text = f'{v["infinitiv"]}, {v["praeteritum"]}, {v["partizip2"]}'
        audio_forms = synth(forms_text, voice=DEFAULT_VOICE)
        media.extend([str(audio_inf), str(audio_forms)])

        deck.add_note(genanki.Note(
            model=VERB_MODEL,
            fields=[
                v["infinitiv"],
                v["praeteritum"],
                v["partizip2"],
                v["helper"],
                v["meaning"],
                f"[sound:{audio_inf.name}]",
                f"[sound:{audio_forms.name}]",
            ],
            tags=["verbs", section_to_tag(v["section"])],
            guid=stable_guid("verb", v["infinitiv"]),
        ))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "verbs.apkg"
    genanki.Package(deck, media_files=media).write_to_file(str(out))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
