"""Print the exact spoken text of each clip, word-accurate to the final cut.

Uses word timings (not segment text) so the output matches what is actually in
the rendered file, and applies the same caption corrections, so this doubles as
copy for the blog post the short is embedded in.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import apply_caption_fixes  # noqa: E402

clips = json.load(open("clips.json"))
transcript = json.load(open("build/transcript.json"))
all_words = [w for s in transcript for w in s["words"]]
only = set(sys.argv[1:]) or None

for c in clips:
    if only and c["id"] not in only:
        continue
    words = apply_caption_fixes(all_words, c.get("caption_fixes"))
    dur = sum(e - s for s, e in c["segments"])
    print(f"\n### {c['id']}  ({dur:.1f}s, layout={c['layout']})")
    print(f"    {c['title']}")
    for i, (s, e) in enumerate(c["segments"]):
        if len(c["segments"]) > 1:
            print(f"  -- segment {i + 1}  [{s:.1f}-{e:.1f}]")
        txt = " ".join(w["w"] for w in words if w["e"] > s and w["s"] < e)
        print(f"    {txt}")
