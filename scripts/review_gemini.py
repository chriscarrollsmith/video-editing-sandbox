"""Second-opinion pass: have Gemini watch each finished short and critique it.

Deliberately runs on the rendered files, not on the plan, so the reviewer sees
what a viewer would see - caption sync, crop, cut seams, audio - rather than
grading my intentions.
"""

import json
import os
import sys
import time

from google import genai
from google.genai import types

MODEL = "gemini-3.6-flash"
OUT = "build/gemini-review.json"

SCHEMA = {
    "type": "object",
    "properties": {
        "hook_strength": {"type": "integer"},
        "hook_note": {"type": "string"},
        "standalone_clarity": {"type": "integer"},
        "clarity_note": {"type": "string"},
        "caption_accuracy": {"type": "integer"},
        "caption_issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string"},
                    "problem": {"type": "string"},
                },
                "required": ["timestamp", "problem"],
            },
        },
        "framing": {"type": "integer"},
        "framing_note": {"type": "string"},
        "edit_quality": {"type": "integer"},
        "edit_note": {"type": "string"},
        "audio": {"type": "integer"},
        "audio_note": {"type": "string"},
        "visible_cut_seams": {"type": "string"},
        "worst_problem": {"type": "string"},
        "concrete_fixes": {"type": "array", "items": {"type": "string"}},
        "publish_ready": {"type": "boolean"},
    },
    "required": [
        "hook_strength", "hook_note", "standalone_clarity", "clarity_note",
        "caption_accuracy", "caption_issues", "framing", "framing_note",
        "edit_quality", "edit_note", "audio", "audio_note",
        "visible_cut_seams", "worst_problem", "concrete_fixes", "publish_ready",
    ],
}

PROMPT = """You are a critical short-form video editor reviewing a vertical \
YouTube Short cut from a 75-minute recorded conference talk (a Google Meet \
recording, so the source is a soft ~1.9 Mbps webcam feed - judge the edit, not \
the inherent source resolution).

The Short will be embedded in a blog post and published to YouTube Shorts.

Clip title: {title}
Intended single idea: {note}
Editor's stated cut points (seconds into the source talk): {segments}
{cutwarn}

Watch and listen to the whole thing, then grade it honestly on 1-5 (5 = best). \
Be specific and harsh; vague praise is useless to me. In particular:

- Do the burned-in captions match the spoken words? Quote any word that is \
wrong, and give the timestamp. This is the thing I most need checked.
- Do captions ever appear out of sync, overlap each other, get cut off at the \
frame edge, or collide with the title bar?
- Does the first 2 seconds earn a viewer stopping the scroll?
- Does the clip make sense with zero context from the rest of the talk?
- Does it end on a complete thought, or does it get chopped mid-sentence?
- Is the speaker's face well framed for a phone, or is the head cropped badly?
- If the clip contains an internal cut, is the seam obvious or distracting? \
Say where you notice it.
- Any audio problems: clipping, abrupt starts, level jumps at a cut?

publish_ready means: I could post this as-is without embarrassment."""


def review(client, path, clip):
    f = client.files.upload(file=path)
    try:
        while f.state.name == "PROCESSING":
            time.sleep(2)
            f = client.files.get(name=f.name)
        if f.state.name == "FAILED":
            raise RuntimeError(f"upload failed for {path}")

        n = len(clip["segments"])
        cutwarn = (
            f"This clip is assembled from {n} source segments, so it contains "
            f"{n - 1} internal jump cut(s)." if n > 1 else
            "This clip is one continuous take with no internal cuts."
        )
        prompt = PROMPT.format(
            title=clip["title"], note=clip.get("note", ""),
            segments=clip["segments"], cutwarn=cutwarn)

        resp = client.models.generate_content(
            model=MODEL,
            contents=[f, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SCHEMA,
            ),
        )
        return json.loads(resp.text)
    finally:
        try:
            client.files.delete(name=f.name)
        except Exception:
            pass


def main():
    client = genai.Client()
    clips = json.load(open("clips.json"))
    only = set(sys.argv[1:]) or None

    results = {}
    if os.path.exists(OUT):
        results = json.load(open(OUT))

    for clip in clips:
        cid = clip["id"]
        if only and cid not in only:
            continue
        path = f"shorts/{cid}.mp4"
        if not os.path.exists(path):
            print(f"skip {cid}: not rendered")
            continue
        for attempt in range(3):
            try:
                results[cid] = review(client, path, clip)
                break
            except Exception as e:
                if attempt == 2:
                    print(f"FAILED {cid}: {e}")
                else:
                    time.sleep(5 * (attempt + 1))
        r = results.get(cid, {})
        if r:
            print(f"{cid:34s} hook={r['hook_strength']} clarity={r['standalone_clarity']} "
                  f"cap={r['caption_accuracy']} frame={r['framing']} edit={r['edit_quality']} "
                  f"audio={r['audio']} ready={r['publish_ready']}")
            json.dump(results, open(OUT, "w"), indent=2)

    json.dump(results, open(OUT, "w"), indent=2)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
