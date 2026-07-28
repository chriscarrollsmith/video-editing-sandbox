"""Transcribe the source talk with word-level timestamps.

Word timings drive both the clip boundary search and the caption burn-in,
so they need to be real timings rather than segment-level interpolation.
"""

import json
import sys

from faster_whisper import WhisperModel

AUDIO = "build/audio/full.wav"
OUT = "build/transcript.json"

model = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=4)

segments, info = model.transcribe(
    AUDIO,
    beam_size=5,
    word_timestamps=True,
    vad_filter=True,
    vad_parameters={"min_silence_duration_ms": 500},
)

print(f"duration={info.duration:.1f}s language={info.language}", flush=True)

out = []
for seg in segments:
    out.append(
        {
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "words": [
                {"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)}
                for w in (seg.words or [])
            ],
        }
    )
    if len(out) % 25 == 0:
        print(f"  {seg.end:7.1f}s / {info.duration:.0f}s  {len(out)} segments", flush=True)

with open(OUT, "w") as f:
    json.dump(out, f, indent=1)

print(f"done: {len(out)} segments -> {OUT}", file=sys.stderr)
