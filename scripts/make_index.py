"""Generate docs/shorts.md - the publishing index for the finished shorts."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import apply_caption_fixes  # noqa: E402

clips = json.load(open("clips.json"))
transcript = json.load(open("build/transcript.json"))
all_words = [w for s in transcript for w in s["words"]]
review = {}
if os.path.exists("build/gemini-review.json"):
    review = json.load(open("build/gemini-review.json"))

THEME_ORDER = ["AI security", "Working with agents", "Building a business", "Breaking into tech"]


def hms(t):
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:04.1f}"


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
         "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout.split()
    return float(out[0]), int(out[1]) / 1e6


lines = [
    "# Shorts index",
    "",
    "Eight vertical shorts cut from the Can Code presentation of 2026-07-23,",
    "grouped into four themes so each theme can carry its own post.",
    "",
    "All files are 1080x1920, H.264 High / AAC, 24 fps, loudness-normalised to",
    "-14 LUFS. Captions are burned in. See `docs/production-notes.md` for how they",
    "were made and `docs/review.md` for the Gemini review pass.",
    "",
    "| # | Short | Length | Theme | Source timecode |",
    "|---|-------|--------|-------|-----------------|",
]

for c in clips:
    path = f"shorts/{c['id']}.mp4"
    dur = sum(e - s for s, e in c["segments"])
    tc = " + ".join(f"{hms(s)}-{hms(e)}" for s, e in c["segments"])
    lines.append(f"| {c['id'][:2]} | `{c['id']}.mp4` | {dur:.0f}s | {c['theme']} | {tc} |")

lines += ["", "---", ""]

for theme in THEME_ORDER:
    group = [c for c in clips if c["theme"] == theme]
    if not group:
        continue
    lines += [f"## {theme}", ""]
    for c in group:
        path = f"shorts/{c['id']}.mp4"
        dur, size = probe(path) if os.path.exists(path) else (0, 0)
        words = apply_caption_fixes(all_words, c.get("caption_fixes"))
        body = " ".join(
            " ".join(w["w"] for w in words if w["e"] > s and w["s"] < e)
            for s, e in c["segments"])
        r = review.get(c["id"], {})

        lines += [
            f"### `{c['id']}.mp4`",
            "",
            f"**Suggested post:** {c['post_title']}  ",
            f"**Slug:** `{c['slug']}`  ",
            f"**Length:** {dur:.1f}s ({size:.1f} MB) · **Layout:** {c['layout']} · "
            f"**Source:** {' + '.join(f'{hms(s)}-{hms(e)}' for s, e in c['segments'])}",
            "",
            f"{c['description']}",
            "",
            f"*Tags:* {', '.join(c['tags'])}",
            "",
        ]
        if len(c["segments"]) > 1:
            lines += [f"> Assembled from {len(c['segments'])} source segments. {c['note']}", ""]
        if r:
            lines += [
                f"*Gemini review:* hook {r['hook_strength']}/5 · clarity "
                f"{r['standalone_clarity']}/5 · captions {r['caption_accuracy']}/5 · framing "
                f"{r['framing']}/5 · edit {r['edit_quality']}/5 · audio {r['audio']}/5 · "
                f"publish-ready: {'yes' if r['publish_ready'] else 'no'}",
                "",
            ]
        lines += ["<details><summary>Transcript</summary>", "", body, "", "</details>", ""]

open("docs/shorts.md", "w").write("\n".join(lines) + "\n")
print("wrote docs/shorts.md")
