# video-editing-sandbox

An experimental sandbox for editing video files.

Currently holds the pipeline that cuts eight vertical shorts out of the Can Code
presentation of 2026-07-23, for embedding in blog posts and publishing to
YouTube Shorts.

## What's here

| Path | |
|---|---|
| `clips.json` | The edit. Cut points, layout, caption corrections, and publishing metadata per clip. |
| `scripts/transcribe.py` | Whisper `small.en` pass over the talk, with word-level timings. |
| `scripts/captions.py` | Word timings → ASS captions with active-word highlighting. |
| `scripts/render.py` | `clips.json` → finished 1080x1920 mp4s. |
| `scripts/review_gemini.py` | Sends each rendered short to `gemini-3.6-flash` for critique. |
| `scripts/make_index.py` | Generates `docs/shorts.md`. |
| `scripts/clip_text.py` | Verbatim text of each clip, word-accurate to the final cut. |
| `docs/shorts.md` | **Start here** — the eight shorts, grouped by theme, with suggested posts, descriptions, tags and transcripts. |
| `docs/production-notes.md` | Source analysis, measured geometry, output spec, caption rules. |
| `docs/review.md` | The Gemini review rounds: what it caught, what I checked and rejected. |
| `reviews/` | Raw review output per round. |
| `transcript.json` | Full transcript of the talk with word timings. |

## Reproducing

The source recording and the rendered shorts are not in git (1.09 GB and
157 MB). With the source alongside as `cancode-presentation-2026-07-23.mp4`:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python \
    faster-whisper google-genai "opencv-python-headless<5" pillow numpy

mkdir -p build/audio build/frames
ffmpeg -i cancode-presentation-2026-07-23.mp4 -vn -ac 1 -ar 16000 build/audio/full.wav
.venv/bin/python scripts/transcribe.py          # ~30 min on 4 cores
.venv/bin/python scripts/render.py              # ~13 min for all eight
GEMINI_API_KEY=... .venv/bin/python scripts/review_gemini.py
.venv/bin/python scripts/make_index.py
```

`render.py` accepts clip ids to render a subset. `ffmpeg` and `ffprobe` must be
on PATH.
