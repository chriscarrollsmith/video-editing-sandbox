---
name: editing-video
description: Use for turning raw video footage into more polished and publishable content.
---

# Editing video

## Before starting

Confirm with the user unless already given: orientation, target length, resolution,
and where output goes. Obtain a `GEMINI_API_KEY` for the review pass, and a
`FAL_KEY` if upscaling. Never commit a key or write one into an artifact.

Needs `ffmpeg`/`ffprobe`, `faster-whisper`, `google-genai`, `fal-client`, and
`opencv-python-headless<5` — 5.x drops the cascade API.

## Survey the source before cutting anything

Never plan an edit from the transcript alone.

1. `ffprobe` for resolution, fps, duration, codecs.
2. Extract a frame every 30 s, tile into contact sheets, and **look at them**.
   Map which ranges are usable and what layout each one uses.
3. Measure crop geometry from pixels — locate panes by finding fully-black rows
   and columns. `cropdetect` fails whenever a bright element touches the frame edge.

Recorded calls change layout mid-talk and switch active speaker on a lag. Verify
who is actually on screen at every intended cut point before rendering.

## Transcribe

faster-whisper, `small.en`, int8, beam 5, `word_timestamps=True`, VAD filter at
500 ms min-silence. Word-level timings are mandatory: segment-level timings
interpolated across a sentence are the usual cause of captions that drift.
Budget ~30 min wall per 75 min of audio on 4 cores.

## Select clips

One idea per clip, self-contained, opening on the thesis rather than the question
or filler preceding it. Cutting an internal tangent beats shipping two ideas.

Prefer "proof of audience" cutaways where they exist — but confirm the reaction
shot is usable first. On recorded calls it is often a camera-off avatar.

Trim points must land exactly on the target word's start time. Starting just
before it drags in the tail of the preceding word when the two are contiguous,
which is audible.

Keep the edit as data: a JSON spec of cut points, layout and per-clip overrides,
with rendering a pure function of it. Review-driven iteration means re-rendering
subsets repeatedly.

## Frame

Talking head: crop to the target aspect at full source height, centred on the
face. Compute the centre per clip from the median of several sampled detections —
a fixed centre sits off-axis when speakers change.

Screen content: never scale a full desktop to phone width. Editor text lands
around 9 px and is unreadable. Crop to the region that matters, or drop the
screen and feature the speaker.

State the upscale ceiling honestly — no framing choice recovers detail the source
never had. Plain Lanczos degrades noticeably past ~4x from a small tile; a
restoration pass (see Upscaling) buys roughly one extra stop of apparent
sharpness, not a new source.

## Caption

Emit ASS, not SRT — positioning and inline colour are both needed.

- Set `PlayResX`/`PlayResY` to the output dimensions so sizes map 1:1 to pixels.
- Size the font as a fraction of frame height (~3.75%), never an absolute value.
  Portrait and landscape need different sizes.
- Chunk for the frame. Portrait: max 6 words, ~2.6 s, two length-balanced lines,
  split on pauses over 0.55 s. Raise the word cap for landscape or captions
  flicker through short chunks.
- Merge a one- or two-word trailing chunk back into its predecessor. A stranded
  final word reads as a dropped word.
- Hold a chunk 0.35 s past its last word but never into the next. Overlapping
  events stack vertically in libass and scramble reading order.
- Chunk each source segment separately so no caption spans an internal cut.
- Rejoin hyphenates — Whisper splits "pre-planning" into two tokens.
- Highlight the spoken word: one Dialogue event per active-word window, the whole
  chunk redrawn with the current word tinted.

**When joining segments, remap word times onto the concatenated output timeline.**
This step, not styling, is what actually produces out-of-sync captions.

Correct mis-transcriptions per clip, anchoring each fix to a timestamp rather
than a string; a global replace corrupts legitimate occurrences elsewhere. Leave
the raw transcript unmodified.

## Encode

Match the source frame rate to avoid resampling judder. `yuv420p`, `+faststart`,
CRF ~20. Normalise audio to -14 LUFS / -1.5 dBTP for YouTube, with short fades at
segment joins to avoid clicks.

## Check your own work before asking for review

Extract frames at every cut point and at known word boundaries, tile them, and
look. This is what catches a clip opening on the wrong person, or a composite
that is illegible at phone size.

## Gemini review pass

Send the rendered files — not the plan — to a current Gemini Flash model.
Enumerate `client.models.list()` to choose one instead of guessing a name.

Request structured output with timestamped, quotable specifics. Ask explicitly
whether captions match the audio, whether the first two seconds earn a stop,
whether the clip ends on a complete thought, and whether internal cuts show.

Triage the response:

- Act on checkable claims: a misheard word, a wrong face, a cold open on filler.
- Verify before acting. Claims about clipped framing and disputed words have
  proven false; re-check against frames or a larger Whisper model.
- Treat 1–5 aesthetic scores as noise. They move between identical runs.
- Never let the reviewer set length or selection policy. It will reject a clip
  for lacking setup, then reject the longer version for having too much.

Two or three rounds converge. Stop there.

## Upscaling

Use a restoration model, not a generation model. `fal-ai/video-upscaler`
(Real-ESRGAN per frame) is verified working on arbitrary recorded footage and is
the default choice.

Verified 2026-07-29 on a 288x240 webcam-tile crop at `scale: 4`:

- Output is exactly 4x (1152x960). Duration, frame rate and frame count are all
  preserved (96 frames in, 96 out), so caption timings stay valid.
- Visibly cleaner than Lanczos plus unsharp — tighter edges, less compression
  mush, and none of the ringing that sharpening introduces. The gain is real but
  moderate: it removes artefacts rather than inventing detail.
- ~44 s of wall time per 4 s of 288x240 input at 4x. Scale that estimate and
  check current pricing before committing to a long clip.

**The returned audio is re-encoded and truncated** — 107 ms short in this test,
while the video kept every frame. Always discard it and re-mux the original
audio (`-map 0:v -map 1:a -c copy`). Verified to restore exact alignment.

Order of operations: upscale first, re-mux original audio, then composite and
burn captions. Never caption before upscaling or the text gets resampled.

Real-ESRGAN is restorative rather than hallucinatory, so it is far safer on
screen recordings than a video model — but it still synthesises detail. Check
small UI text for legibility instead of assuming it survived.

## Background removal

`veed/video-background-removal/fast` extracts the subject with no green screen.
Use it when a landscape source has to fill a vertical frame: compositing a cutout
onto a designed backdrop fills 9:16 without upscaling the subject past its
quality ceiling, because the background costs no resolution. This is the fix for
"speaker in a letterboxed box with black bars above and below".

Verified 2026-07-29 on a 1152x960 clip, `output_codec: vp9`,
`refine_foreground_edges: true`:

- Matte quality is good on a soft webcam source — clean edges at the head and
  shoulders, ~42% opaque / 57% clear.
- ~22 s wall time for 96 frames. Priced per 30 frames, refinement costing ~50%
  more; roughly 1 cent per second of 24 fps footage.
- Set `subject_is_person: false` for non-people. Do not use it on screen
  recordings — the segmentation is subject-oriented and has nothing to hold onto.

Three ffmpeg traps, all verified:

1. `ffprobe` reports `pix_fmt=yuv420p` and `alphaextract` fails, but the alpha is
   there — look for `TAG:ALPHA_MODE=1`. Force `-c:v libvpx-vp9` on the input or
   it decodes opaque.
2. **Even with the forced decoder, a filtergraph silently drops the alpha.**
   `overlay` then composites nothing and you get a bare background. Decode to raw
   RGBA and pipe it into a second ffmpeg (`-pix_fmt rgba -f rawvideo -` into
   `-f rawvideo -pix_fmt rgba -s WxH -r N -i -`), or write RGBA frames first.
   Both work; inline does not.
3. Output is **shorter than input** — 96 frames in, 93 out, with audio
   re-encoded to Opus. The loss is end-truncation, not distributed drops
   (confirmed by matching frames 0, 46 and 92 between input and output), so
   earlier caption timings stay valid. Re-mux the original audio and account for
   the clipped tail.

### Veo is not an upscaler

Two different things share the Veo name. Do not conflate them.

**`generate_videos` with a video source is extension, not upscaling.** Verified
on the Gemini Developer API, 2026-07-28: `veo-3.1-lite-generate-preview` refuses
video input outright (*"Video extension is not allowed for this model"*), and the
full and fast variants accept only video Veo itself produced (*"Input video must
be a video that was generated by VEO that has been processed"*). Recorded footage
cannot be fed in. Attaching an "upscale this" prompt to this path does nothing.

**A standalone Veo upscaling capability exists on Vertex AI**, announced
2026-04-03, documented as enhancing video to 1080p and 4K regardless of whether
Veo, another model, or a camera produced it. It is a separate API surface, not
`generate_videos` with a prompt. It was **private preview** at announcement —
assume no access until a call actually succeeds. Not verified here; the session
that established the above had no GCP credentials, so the Vertex path is
documentation only.

Surfaces differ — confirm which one you are on:

- Model IDs are `veo-3.1-lite-generate-001` on Vertex, `veo-3.1-lite-generate-preview`
  on the Gemini API.
- Vertex lists "Extend videos: Supported" for 3.1 Lite while the Gemini API
  rejects extension for that model, and the same Vertex page marks the video
  modality "output only". Trust a probe over the capability table.
- Vertex 3.1 Lite generation: 4, 6 or 8 s, 24 fps, 9:16 or 16:9, 720p/1080p,
  us-central1 only. 4K comes from the upscaler, not from generation.

If you get upscaler access:

- The 8 s ceiling is a *generation* limit. Do not assume it binds the upscaler;
  check its own duration limit before chunking and stitching.
- Caption after upscaling, never before, so text is never resampled.
- Before reusing caption timings, confirm the returned clip has the same duration
  and frame rate as the input. Any drift invalidates them.

Gemini API quirks when passing Veo-generated video: inline bytes are rejected
(`encodedVideo` unsupported), so pass a Files API URI; and `Video.from_file()`
attaches a mime type serialised as `encoding`, which is also rejected.

Never run a *generative* video model as an upscaler over a screen recording — it
reconstructs UI text into plausible nonsense. Prefer the Real-ESRGAN path above.

