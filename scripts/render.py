"""Render vertical (1080x1920) shorts from the source talk.

Two layouts:
  head   - face-centred 9:16 crop of a full-frame webcam segment
  screen - stacked composite: speaker tile above, shared-screen region below,
           over a blurred fill of the screen content

A clip is one or more source segments concatenated, so a clip can drop a
tangent in the middle and keep the parts that matter. Everything is done in a
single encode: segments come in as separate fast-seeked inputs, get concatenated,
then the layout and captions are applied once.
"""

import json
import os
import subprocess
import sys

import cv2

SRC = "cancode-presentation-2026-07-23.mp4"
OUT_DIR = "shorts"
BUILD = "build"
W, H = 1080, 1920

# Source geometry, measured from the recording (see docs/production-notes.md).
SHARE = (1440, 816, 0, 132)      # w, h, x, y  - shared-screen pane
TILE = (477, 270, 1443, 405)     # w, h, x, y  - speaker thumbnail during share

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from captions import build_ass  # noqa: E402


def face_center_x(segments, samples=9):
    """Median horizontal face centre across the clip, for crop placement."""
    casc = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    total = sum(e - s for s, e in segments)
    xs = []
    for i in range(samples):
        # walk a fraction of the way through the concatenated duration
        want = total * (i + 0.5) / samples
        for s, e in segments:
            if want <= e - s:
                t = s + want
                break
            want -= e - s
        png = f"{BUILD}/frames/_fc.png"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", SRC,
             "-frames:v", "1", png], check=True)
        img = cv2.imread(png)
        if img is None:
            continue
        faces = casc.detectMultiScale(
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.15, 6, minSize=(120, 120))
        if len(faces):
            x, y, w, h = max(faces.tolist(), key=lambda r: r[2] * r[3])
            xs.append(x + w // 2)
    if not xs:
        return 1920 // 2
    xs.sort()
    return xs[len(xs) // 2]


def head_filter(cx):
    """9:16 crop centred on the face, upscaled to 1080x1920."""
    cw = 608  # 1080 * 9/16, rounded to even
    x = max(0, min(1920 - cw, int(cx - cw / 2)))
    return (f"crop={cw}:1080:{x}:0,scale={W}:{H}:flags=lanczos,"
            f"unsharp=5:5:0.4:5:5:0.0,setsar=1")


# Hero crop inside the speaker tile: 3:2, centred on the measured face position
# (x~237 of 477) and stopping above the Meet name label in the bottom ~30 px.
TILE_HERO = (288, 240, 1443 + 93, 405 + 0)


def tile_filter(src, hero_y=520, hero_w=1080):
    """Speaker thumbnail promoted to hero, over a blurred fill of itself.

    Used for segments recorded during screen share where the shared desktop is
    a dark, static IDE - blurring that gives near-black dead space and the
    screen content is illegible at any size that fits a phone.
    """
    tw, th, tx, ty = TILE
    hw, hh, hx, hy = TILE_HERO
    hero_h = int(round(hero_w * hh / hw / 2) * 2)
    return (
        f"[{src}]split=2[t1][t2];"
        # Blurred hard enough that it reads as an ambient wash rather than a
        # recognisable second copy of the speaker's face.
        f"[t1]crop={tw}:{th}:{tx}:{ty},scale=240:-2,boxblur=18:3,"
        f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=bilinear,"
        f"crop={W}:{H},eq=brightness=-0.34:saturation=0.40:contrast=0.85,"
        f"vignette=PI/4[bg];"
        f"[t2]crop={hw}:{hh}:{hx}:{hy},scale={hero_w - 8}:{hero_h - 8}:flags=lanczos,"
        f"unsharp=7:7:0.8:7:7:0.0,pad=iw+8:ih+8:4:4:0x2a2a2aff[hero];"
        f"[bg][hero]overlay=(W-w)/2:{hero_y},setsar=1"
    )


def screen_filter(src, screen_crop=None, screen_box=(1080, 700), screen_y=900,
                  tile_w=800, tile_y=250):
    """Speaker tile stacked above the shared-screen region on a blurred fill."""
    sw, sh, sx, sy = SHARE
    if screen_crop:
        cw, ch, cx, cy = screen_crop
        sx, sy, sw, sh = sx + cx, sy + cy, cw, ch
    bw, bh = screen_box
    tw, th, tx, ty = TILE
    tile_h = int(round(tile_w * th / tw / 2) * 2)

    return (
        f"[{src}]split=3[s1][s2][s3];"
        f"[s1]crop={sw}:{sh}:{sx}:{sy},scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},boxblur=32:2,eq=brightness=-0.24:saturation=0.6[bg];"
        f"[s2]crop={sw}:{sh}:{sx}:{sy},scale={bw}:{bh}:force_original_aspect_ratio=decrease:"
        f"flags=lanczos,unsharp=5:5:0.6:5:5:0.0,pad=iw+8:ih+8:4:4:0x1f1f1fff[scr];"
        f"[s3]crop={tw}:{th}:{tx}:{ty},scale={tile_w}:{tile_h}:flags=lanczos,"
        f"unsharp=5:5:0.4:5:5:0.0,pad=iw+8:ih+8:4:4:0x1f1f1fff[tile];"
        f"[bg][tile]overlay=(W-w)/2:{tile_y}[a];"
        f"[a][scr]overlay=(W-w)/2:{screen_y},setsar=1"
    )


def apply_caption_fixes(words, fixes):
    """Correct individual mis-transcribed words before they are burned in.

    Each fix targets the word whose start time is nearest `at`, so a correction
    stays pinned to one spot instead of rewriting every occurrence in the talk.
    Trailing punctuation from the original token is preserved.
    """
    if not fixes:
        return words
    words = [dict(w) for w in words]
    for fix in fixes:
        i = min(range(len(words)), key=lambda j: abs(words[j]["s"] - fix["at"]))
        old = words[i]["w"]
        tail = "".join(c for c in old[len(old.rstrip(".,?!;:")):])
        words[i]["w"] = fix["to"] + tail
    return words


def render(clip, words):
    cid = clip["id"]
    segs = [tuple(s) for s in clip["segments"]]
    ass_path = f"{BUILD}/{cid}.ass"
    out = f"{OUT_DIR}/{cid}.mp4"

    words = apply_caption_fixes(words, clip.get("caption_fixes"))
    with open(ass_path, "w") as f:
        f.write(build_ass(words, segs, title=clip.get("overlay_title")))
    ass_arg = ass_path.replace(":", r"\:")

    cmd = ["ffmpeg", "-y", "-v", "error"]
    for s, e in segs:
        cmd += ["-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", SRC]

    n = len(segs)
    parts = []
    if n > 1:
        streams = "".join(f"[{i}:v][{i}:a]" for i in range(n))
        parts.append(f"{streams}concat=n={n}:v=1:a=1[cv][ca]")
        vsrc, asrc = "cv", "ca"
    else:
        vsrc, asrc = "0:v", "0:a"

    if clip["layout"] == "head":
        cx = clip.get("crop_cx") or face_center_x(segs)
        clip["_crop_cx"] = cx
        parts.append(f"[{vsrc}]{head_filter(cx)}[lay]")
    elif clip["layout"] == "tile":
        parts.append(
            tile_filter(vsrc, hero_y=clip.get("hero_y", 520),
                        hero_w=clip.get("hero_w", 1080)) + "[lay]")
    else:
        parts.append(
            screen_filter(
                vsrc,
                screen_crop=clip.get("screen_crop"),
                screen_box=tuple(clip.get("screen_box", (1080, 700))),
                screen_y=clip.get("screen_y", 900),
                tile_w=clip.get("tile_w", 800),
                tile_y=clip.get("tile_y", 250),
            ) + "[lay]")

    parts.append(f"[lay]ass={ass_arg}[v]")
    # Short fades top and tail, and loudness normalisation to YouTube's target.
    parts.append(
        f"[{asrc}]loudnorm=I=-14:TP=-1.5:LRA=11,"
        f"afade=t=in:st=0:d=0.06,areverse,afade=t=in:st=0:d=0.10,areverse[a]")

    cmd += [
        "-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", "24", "-g", "48",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", out,
    ]
    subprocess.run(cmd, check=True)
    return out


def main():
    clips = json.load(open("clips.json"))
    transcript = json.load(open(f"{BUILD}/transcript.json"))
    words = [w for seg in transcript for w in seg["words"]]

    os.makedirs(OUT_DIR, exist_ok=True)
    only = set(sys.argv[1:]) or None
    for clip in clips:
        if only and clip["id"] not in only:
            continue
        out = render(clip, words)
        dur = sum(e - s for s, e in clip["segments"])
        size = os.path.getsize(out) / 1e6
        print(f"{clip['id']:34s} {dur:5.1f}s  {size:5.1f} MB  {out}")


if __name__ == "__main__":
    main()
