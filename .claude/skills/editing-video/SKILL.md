---
name: editing-video
description: Use for turning raw video footage into more polished and publishable content.
---

# Editing video

Pipeline order. Steps in brackets are optional and cost money.

survey → transcribe → select cuts → [restore] → [matte] → frame and composite →
burn captions → encode → verify yourself → review

Captions go on last, after any external pass, or the text gets resampled.

## Before starting

Confirm unless already given: orientation, target length, resolution, and where
output goes. Obtain a `GEMINI_API_KEY` for the review pass and a `FAL_KEY` for
the optional passes. Never commit a key or write one into an artifact.

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

No framing choice recovers detail the source never had. Lanczos degrades
noticeably past ~4x from a small tile. Restoration buys about one extra stop of
apparent sharpness; matting onto a backdrop avoids needing the upscale at all.

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

## Optional passes (fal)

Both cost money and both hand back re-encoded audio. Get user approval with a
cost estimate first, and after either pass:

- **Discard the returned audio and re-mux the original** (`-map 0:v -map 1:a
  -c copy`).
- Compare frame count and duration against the input before trusting existing
  caption timings.

### Restoration — `fal-ai/video-upscaler`

Real-ESRGAN per frame. Works on arbitrary recorded footage. Verified 2026-07-29
on a 288x240 webcam-tile crop at `scale: 4`:

- Exactly 4x out (1152x960), with duration, frame rate and frame count all
  preserved (96 in, 96 out).
- Visibly cleaner than Lanczos plus unsharp — tighter edges, none of the ringing
  sharpening introduces. It removes artefacts rather than inventing detail.
- ~44 s wall time per 4 s of 288x240 at 4x.
- Audio came back 107 ms short despite every video frame surviving.

Restorative rather than hallucinatory, so far safer on screen recordings than a
video model — but it still synthesises detail. Check small UI text for legibility
instead of assuming it survived.

### Matting — `veed/video-background-removal/fast`

Subject extraction, no green screen. Use it when a landscape source has to fill a
vertical frame: compositing a cutout onto a designed backdrop fills 9:16 without
upscaling the subject past its ceiling, because the background costs no
resolution. This is the fix for a speaker letterboxed between black bars.

Verified 2026-07-29 on a 1152x960 clip, `output_codec: vp9`,
`refine_foreground_edges: true`:

- Good matte on a soft webcam source — clean head and shoulder edges, ~42%
  opaque.
- ~22 s wall time for 96 frames. Priced per 30 frames, refinement ~50% more;
  roughly a cent per second of 24 fps footage.
- Set `subject_is_person: false` for objects. Useless on screen recordings — the
  segmentation has nothing to hold onto.
- 96 frames in, 93 out, audio re-encoded to Opus. The loss is end-truncation, not
  distributed drops (confirmed by matching frames 0, 46 and 92), so existing
  caption timings survive; only the tail goes.

Three ffmpeg traps on the alpha, all verified:

1. `ffprobe` reports `pix_fmt=yuv420p` and `alphaextract` fails, but the alpha is
   there — look for `TAG:ALPHA_MODE=1`. Force `-c:v libvpx-vp9` on input or it
   decodes opaque.
2. **Even with the forced decoder, a filtergraph silently drops the alpha.**
   `overlay` composites nothing and returns a bare background, with no error.
   Decode to raw RGBA and pipe into a second ffmpeg (`-pix_fmt rgba -f rawvideo -`
   into `-f rawvideo -pix_fmt rgba -s WxH -r N -i -`), or write RGBA frames first.
3. Swapping the real room for a synthetic backdrop is an editorial change, not
   just a technical one. Confirm it suits the register before applying it.

## Veo is not an upscaler

Do not spend time here. `generate_videos` with a video source is *extension*, and
only of Veo's own output — verified 2026-07-28 on the Gemini Developer API, where
`veo-3.1-lite-generate-preview` refuses video input outright and the full and fast
variants reject anything Veo did not generate. Recorded footage cannot be fed in,
and an "upscale this" prompt on that path does nothing.

A separate Veo upscaling capability was announced for Vertex AI on 2026-04-03,
handling 1080p and 4K on footage from any source. It is a different API surface,
was private preview at announcement, and is unverified here — assume no access
until a call succeeds. Model IDs differ by surface (`-generate-001` on Vertex,
`-generate-preview` on the Gemini API), as do the advertised capabilities; trust
a probe over the capability table.

Never use a generative video model as an upscaler on a screen recording. It
reconstructs UI text into plausible nonsense.
