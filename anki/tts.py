"""edge-tts wrapper with on-disk caching.

Generates MP3s for German text using Microsoft Edge's neural TTS.
Cached by sha1(voice|text) so re-running the build is free.
"""
import asyncio
import hashlib
from pathlib import Path

import edge_tts

DEFAULT_VOICE = "de-DE-KatjaNeural"
CACHE_DIR = Path(__file__).parent / "audio"


async def _synth_async(text: str, voice: str, out_path: Path) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))


def synth(text: str, voice: str = DEFAULT_VOICE) -> Path:
    """Synthesize `text` with `voice`, return cached MP3 path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(f"{voice}|{text}".encode("utf-8")).hexdigest()[:16]
    out = CACHE_DIR / f"{digest}.mp3"
    if not out.exists():
        asyncio.run(_synth_async(text, voice, out))
    return out


if __name__ == "__main__":
    import sys
    path = synth(sys.argv[1] if len(sys.argv) > 1 else "Hallo, wie geht es dir?")
    print(path)
