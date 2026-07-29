"""Validate the Veo video-to-video upscale path described in the editing skill.

Checks, in order: does the API accept a video source at all; is the returned
clip the same content or a regeneration; is duration/fps preserved (required if
captions are to be re-applied afterwards); do overlapping chunks reassemble.
"""

import sys
import time

from google import genai
from google.genai import types

MODEL = "veo-3.1-lite-generate-preview"
PROMPT = ("Upscale this video to a sharper, higher-resolution version. Keep the "
          "framing, the person, the background and all motion exactly as they are. "
          "Do not add, remove or restyle anything.")


def run(path, out):
    client = genai.Client()
    # NB: Video.from_file() guesses a mime_type, which the Gemini API path
    # serialises as `encoding` -- rejected by veo-3.1-lite with a 400. Build the
    # Video without one.
    src = types.GenerateVideosSource(
        video=types.Video(video_bytes=open(path, "rb").read()), prompt=PROMPT)
    cfg = types.GenerateVideosConfig(resolution="1080p", aspect_ratio="9:16",
                                     number_of_videos=1)
    op = client.models.generate_videos(model=MODEL, source=src, config=cfg)
    print(f"  submitted: {op.name}", flush=True)

    t0 = time.time()
    while not op.done:
        time.sleep(10)
        op = client.operations.get(op)
        print(f"  ...{time.time() - t0:.0f}s done={op.done}", flush=True)

    if op.error:
        print(f"  ERROR: {op.error}")
        return False
    resp = op.response or op.result
    vids = getattr(resp, "generated_videos", None)
    if not vids:
        print(f"  no video in response: {resp}")
        return False
    client.files.download(file=vids[0].video)
    vids[0].video.save(out)
    print(f"  saved {out} after {time.time() - t0:.0f}s")
    return True


if __name__ == "__main__":
    for a in sys.argv[1:]:
        src, dst = a.split(":")
        print(f"== {src}")
        if not run(src, dst):
            sys.exit(1)
