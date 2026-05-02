# German Study Kit — Roadmap

Self-study plan from solid A1 to B2, anchored to **2026-05-01**.

| Level | Target date | Window | Focus |
|---|---|---|---|
| A2 | 2026-08-01 | 3 months | Past tense, modal verbs, dative, separable verbs, daily-life sentences |
| B1 | 2027-05-01 | +9 months | Konjunktiv II, Passiv, subordinate clauses, opinion-giving |
| B2 | 2028-05-01 | +12 months | Konnektoren, formal register, abstract topics, exam strategy |

## Daily routine (20-30 min Anki + 20-30 min listening)

- **Anki**: ~10 new cards/day, all reviews due. Decks built from `grammar/<level>/*.md`.
- **Listening**: see [listening.md](listening.md). Currently: Coffee Break German + Slow German.

## Curriculum source

*Grammatik aktiv A1-B1* (Cornelsen). Each chapter → one markdown file under `grammar/A1/` or `grammar/A2/`. Topics ordered by textbook chapter number.

## Card design

For every topic file, the build produces **three** card types per sentence:

1. **Cloze** — `Ich {{c1::bin}} müde.` with audio. Back: full sentence + English + grammar note.
2. **EN → DE production** — Front: English. Back: German + audio + grammar note.
3. **Listening (audio-only)** — Front: just the audio (with hint "Hör zu und übersetze"). Back: German text + English + grammar note. Trains your ear without leaning on reading.

Voice: `de-DE-KatjaNeural` (edge-tts).

## Deck structure

Each `.apkg` creates a hierarchy in Anki: `German::<level>::<NN topic>`. So A1 expands into 16 subdecks:

```
German::A1::01 Personalpronomen + sein (Präsens)
German::A1::02 haben (Präsens)
German::A1::03 Regelmäßige Verben (Präsens)
…
```

Why per-topic subdecks: **read the grammar `.md` first, then study only that topic's subdeck in Anki.** Don't mix all 16 A1 topics into one review queue until you've internalized each one.

If 3 cards per sentence is too many for your daily review budget, suspend the "German Listening (audio-only front)" note type in Anki — your scheduling on the other two card types is unaffected.

## Build

```bash
make install   # one-time: venv + deps
make a1        # build A1 deck → anki/out/A1.apkg
make a2        # build A2 deck → anki/out/A2.apkg
make b1        # build B1 deck → anki/out/B1.apkg
make b2        # build B2 deck → anki/out/B2.apkg
make verbs     # build irregular-verbs deck → anki/out/verbs.apkg
make themen    # build thematic deck → anki/out/themen.apkg
make all       # build everything
```

Import the `.apkg` into Anki. Re-running `make` is safe — audio is cached in `anki/audio/`.

## Status

- **A1**: 16 topics × 20 sentences × 3 cards = ~960 cards. ✅ shipped in `anki/out/A1.apkg`.
- **A2**: 18 topics × 20 sentences × 3 cards = ~1080 cards. ✅ shipped in `anki/out/A2.apkg`.
- **B1**: 18 topics × 20 sentences × 3 cards = ~1080 cards. ✅ shipped in `anki/out/B1.apkg`.
- **B2**: 18 topics × 20 sentences × 3 cards = ~1080 cards. ✅ shipped in `anki/out/B2.apkg`.
- **Verbs**: 80 unregelmäßige Verben (Infinitiv + Präteritum + Partizip II + helper). ✅ shipped in `anki/out/verbs.apkg`.
- **Themen**: 12 Alltagsthemen × ~15-30 Sätze = 215 Sätze × 2 cards (EN→DE + DE→EN) = ~430 cards. ✅ shipped in `anki/out/themen.apkg`.

## Reference & exam material (not Anki — markdown only)

- [resources.md](resources.md) — curated apps, podcasts, YouTube channels, dictionaries, tutoring platforms, by skill and by level
- [reference/irregular-verbs.md](reference/irregular-verbs.md) — source for the verbs deck, doubles as a quick lookup
- [reference/konnektoren.md](reference/konnektoren.md) — every connector across A2-B2 in one page, with word-order rules
- [exam/A2.md](exam/A2.md) — Goethe-Zertifikat A2 format & prep plan
- [exam/B1.md](exam/B1.md) — Goethe-Zertifikat B1 format & prep plan
- [exam/B2.md](exam/B2.md) — Goethe-Zertifikat B2 format & prep plan
- [listening.md](listening.md) — podcast curriculum (older quick-reference; superseded by resources.md but kept for tagged level lookups)

## Scope

A1 + A2 first. B1 after A2 lands. B2 after B1.
