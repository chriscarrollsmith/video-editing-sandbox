---
name: editing-video
description: Use for turning raw video footage into more polished and publishable content.
---

# Editing video

## Before starting

Confirm with the user unless already given: orientation, target length, resolution,
and where output goes. Obtain a `GEMINI_API_KEY` if not in the environment; never
commit it or write it into an artifact.

Needs `ffmpeg`/`ffprobe`, `faster-whisper`, `google-genai`, and
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

State the upscale ceiling honestly. Past roughly 4x from a small source tile the
result is mush, and no framing choice recovers detail the source never had.

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

## Upscaling is not available through Veo

Verified against the Gemini API on 2026-07-28:

- `veo-3.1-lite-generate-preview` rejects video input outright — *"Video
  extension is not allowed for this model."*
- `veo-3.1-generate-preview` and `veo-3.1-fast-generate-preview` accept video
  only if Veo produced it — *"Input video must be a video that was generated by
  VEO that has been processed."*

Veo's video input is a continuation feature for Veo's own output, not
video-to-video. Recorded footage cannot be fed in, so chunking into 8 s windows
with 1 s overlap and re-applying captions afterwards does not apply. Do not
budget for it.

Two API details if working with Veo-generated input anyway: inline bytes are
rejected on the Gemini API path (`encodedVideo` unsupported), so pass a Files API
URI; and `Video.from_file()` attaches a mime type the API rejects as `encoding`.

For real upscaling use a dedicated restorer (Real-ESRGAN, Topaz). Never run a
generative upscaler over a screen recording — it reconstructs text into plausible
nonsense.
