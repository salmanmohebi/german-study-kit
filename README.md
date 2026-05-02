# German Study Kit

A reproducible Anki deck pipeline for learning German from **A1 to B2**. Markdown source files compile into `.apkg` decks with TTS audio for every sentence — no manual card creation.

Built for self-study, but anyone can use it. If you just want to study, jump to [Quickstart](#quickstart). If you want to edit content or fork the kit, see [Building from source](#building-from-source).

## What's inside

Six Anki decks, ~4 700 cards total, all with neural TTS audio (`de-DE-KatjaNeural` via Microsoft Edge).

| Deck | Topics | Cards | Description |
|---|---|---|---|
| `A1.apkg` | 16 grammar | ~960 | Personalpronomen, modals, Akkusativ, trennbare Verben, Perfekt, … |
| `A2.apkg` | 18 grammar | ~1 080 | Dativ, Wechselpräpositionen, Adjektivdeklination, Nebensätze, Konjunktiv II höflich |
| `B1.apkg` | 18 grammar | ~1 080 | Konjunktiv II, Passiv, Genitiv, Relativsätze, Plusquamperfekt, Konnektoren |
| `B2.apkg` | 18 grammar | ~1 080 | Konjunktiv I, Partizipien, Doppelinfinitiv, Funktionsverbgefüge, Nebensätze (vertieft) |
| `verbs.apkg` | 80 verbs | 80 | Top irregular verbs with all three principal parts + helper |
| `themen.apkg` | 12 packs | ~430 | Survival German + 11 daily-life situations (restaurant, hotel, doctor, …) |

Plus markdown reference docs (no Anki): connectors cheat sheet, Goethe exam prep at every level, curated learning resources.

## Quickstart

If you just want to study:

1. Install [Anki](https://apps.ankiweb.net/) (free desktop app, also iOS/Android).
2. Download the `.apkg` files from [`anki/out/`](anki/out/) in this repo.
3. In Anki: **File → Import** → pick the `.apkg`. Done.

Each `.apkg` imports as a hierarchy: `German::<level>::<NN topic>`. So A1 expands into 16 subdecks (`German::A1::01 Personalpronomen + sein`, `German::A1::02 haben`, …). You can study **one topic at a time** — read its `.md` file in [`grammar/`](grammar/) for the rule, then study just that subdeck in Anki.

## How the cards look

Every grammar sentence produces **three card types** for thorough learning:

| Card type | Front | Back |
|---|---|---|
| **Cloze drill** | German with one word blanked + audio | full German sentence + English + grammar note |
| **EN → DE production** | English sentence | German + audio + grammar note |
| **Audio-only listening** | just plays the audio | German text + English + grammar note |

The **verbs deck** has one card per verb: infinitive on front, three principal parts (with helper) on back.

The **themen deck** has two cards per sentence: EN→DE and DE→EN, no cloze.

## What makes this different from other German Anki decks

- **Sentence-based, not vocabulary-based** — you learn grammar through 20 example sentences per topic, not by drilling rules in isolation.
- **Audio for every sentence** — neural TTS, not robotic. Listening cards train comprehension explicitly.
- **Markdown source-of-truth** — edit a `.md` file, run `make`, get an updated `.apkg`. Stable card GUIDs preserve your Anki review schedule across rebuilds.
- **Goethe-aligned curriculum** — topics map to *Grammatik aktiv A1-B1* (Cornelsen) and standard B2 syllabus. Exam prep schedules included.
- **Free** — no subscription, no API keys. `edge-tts` is free.

## Building from source

If you want to edit content or rebuild from scratch:

```bash
git clone https://github.com/salmanmohebi/german-study-kit.git
cd german-study-kit
make install        # one-time: .venv + dependencies
make a1             # build one level
make all            # build everything (A1 + A2 + B1 + B2 + verbs + themen)
```

Audio is cached in `anki/audio/` (gitignored). Only changed sentences hit the TTS API on rebuild — the rest is instant.

Requirements: **Python 3.11+**, `make`, internet (for first audio fetch).

## Repository structure

```
german-study-kit/
├── grammar/                  # markdown source for grammar decks
│   ├── A1/                   # 16 topic files
│   ├── A2/                   # 18 topic files
│   ├── B1/                   # 18 topic files
│   └── B2/                   # 18 topic files
├── themen/                   # 12 thematic packs (survival, restaurant, hotel, …)
├── reference/
│   ├── irregular-verbs.md    # source for verbs deck + lookup table
│   └── konnektoren.md        # connector cheat sheet (A2-B2)
├── exam/
│   ├── A2.md                 # Goethe-Zertifikat A2 format & prep schedule
│   ├── B1.md                 # B1 format & prep
│   └── B2.md                 # B2 format & prep
├── anki/
│   ├── build.py              # grammar deck builder
│   ├── build_verbs.py        # verbs deck builder
│   ├── build_themen.py       # thematic deck builder
│   ├── tts.py                # edge-tts wrapper with on-disk caching
│   ├── audio/                # cached mp3s (gitignored)
│   └── out/                  # built .apkg files (committed)
├── resources.md              # curated apps, podcasts, YouTube, tutoring platforms
├── roadmap.md                # study plan, daily routines, scope
├── listening.md              # podcast curriculum by level
├── Makefile
└── requirements.txt
```

## Customizing the kit

### Add or edit a grammar topic

Each topic is a single markdown file:

````markdown
---
title: Personalpronomen + sein (Präsens)
level: A1
topic_id: a1-01-sein
tags: [a1, sein, personalpronomen]
---

## Erklärung

(Short grammar explanation. Rendered as HTML on the back of every card.)

## Sätze

- Ich {{c1::bin}} müde. | I am tired.
- Du {{c1::bist}} sehr nett. | You are very nice.
````

Format rules:
- `## Erklärung` → grammar note shown on the back of every card from this file.
- `## Sätze` → list of `- <German> | <English>` pairs.
- Cloze markup `{{c1::word}}` produces a fill-in-the-blank card.
- Multi-cloze (`{{c1::}}` + `{{c2::}}` in the same sentence) generates separate cards per blank.

Run `make a1` (or `a2`/`b1`/`b2`) to rebuild.

### Add a thematic pack

Drop a new file in `themen/` with the same markdown format. Cloze markup is optional. Each sentence becomes 2 cards (EN→DE + DE→EN).

### Change the TTS voice

Edit `DEFAULT_VOICE` in [`anki/tts.py`](anki/tts.py). Other German voices:

- `de-DE-KatjaNeural` *(default, female)*
- `de-DE-ConradNeural` *(male)*
- `de-DE-AmalaNeural` *(female, younger)*
- `de-DE-BerndNeural` *(male, older)*

Delete `anki/audio/` to force regeneration with the new voice.

## Study guides included

| File | What's there |
|---|---|
| [`roadmap.md`](roadmap.md) | Overall plan, daily routine, deck status |
| [`resources.md`](resources.md) | Curated apps, podcasts, YouTube, tutors, dictionaries (per level) |
| [`exam/A2.md`](exam/A2.md), [`exam/B1.md`](exam/B1.md), [`exam/B2.md`](exam/B2.md) | Goethe-Zertifikat format + week-by-week prep schedules |
| [`reference/konnektoren.md`](reference/konnektoren.md) | Every connector across A2-B2 with word-order rules |
| [`reference/irregular-verbs.md`](reference/irregular-verbs.md) | 80 verbs principal parts |

## Stack

- [`edge-tts`](https://github.com/rany2/edge-tts) — free neural TTS via Microsoft Edge's voice service (no API key)
- [`genanki`](https://github.com/kerrickstaley/genanki) — programmatic `.apkg` generation
- [`PyYAML`](https://pyyaml.org/) + [`markdown`](https://python-markdown.github.io/) — frontmatter parsing + grammar note rendering
- Python 3.11+

## Acknowledgments

- Grammar curriculum based on *Grammatik aktiv A1-B1* (Cornelsen) plus standard Goethe-Zertifikat B2 syllabus.
- TTS by Microsoft Edge neural voices (Katja).
- Inspired by Refold-style sentence mining + spaced repetition.

## Contributing

Found a German error, awkward sentence, or grammar inaccuracy? PRs welcome — edit the relevant markdown file in `grammar/`, `themen/`, or `reference/`, run `make` to verify the build, and submit.
