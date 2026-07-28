# Production notes — Can Code presentation, 2026-07-23

## Source

| | |
|---|---|
| File | `cancode-presentation-2026-07-23.mp4` (1.09 GB, not committed) |
| Container | MP4, H.264 High + AAC-LC |
| Video | 1920x1080, 24 fps, ~1.89 Mbps |
| Audio | 48 kHz stereo, 128 kbps |
| Duration | 4512.3 s (1:15:12) |

It is a Google Meet recording, so the frame is whatever Meet composited at the
time. Three distinct layouts appear, and they determine how a segment can be
reframed vertically.

## Layout map

Derived from a frame-every-30s scan (`build/scan/`, contact sheets in
`build/sheet*.jpg`).

| Range | Layout | Usable for shorts |
|---|---|---|
| 00:00 – 05:00 | Full-frame webcam, alternating speakers | Yes |
| 05:00 – 28:00 | Screen share + speaker thumbnail | Yes, with the stacked composite |
| 28:00 – 54:00 | Full-frame webcam, mostly Christopher Smith | Best material |
| 54:00 – 1:15:12 | A participant's camera pointed at the ceiling | **No** — unusable |

The final 21 minutes are a ceiling shot for the whole duration. Whatever is said
there cannot carry a short on its own, so nothing is sourced from it.

Camera-off participants show as a coloured initial on black (33:30, 38:30,
1:01:00). Those are hard cut points, useful as segment boundaries.

## Measured geometry

Taken from pixel analysis of full-resolution frames, not from cropdetect —
`cropdetect` is defeated here because the bright participant thumbnail reaches
the frame edge.

Screen-share layout (stable for the whole 05:00–28:00 block):

- A black gutter at columns 1440–1442 splits the frame.
- **Shared screen pane**: `1440x816` at `(0, 132)` — a 16:9 desktop letterboxed
  into the left region.
- **Speaker thumbnail**: `477x270` at `(1443, 405)` — also 16:9.

Both are exposed in `scripts/render.py` as `SHARE` and `TILE`.

The small grid of participant faces visible around 13:00–21:30 is *inside* the
shared screen — the presenter was sharing a desktop with the Meet window on it —
not a separate Meet pane.

## Output spec

1080x1920 (9:16), H.264 High, CRF 20, `yuv420p`, 24 fps (source rate, so no
frame resampling), GOP 48. Audio AAC 192 kbps 48 kHz stereo, loudness-normalised
to -14 LUFS / -1.5 dBTP, which is what YouTube targets.

### Layout `head`

A 608x1080 crop (exactly 9:16 of the full frame height) centred on the speaker's
face, upscaled to 1080x1920 with Lanczos and a light unsharp pass. The crop x is
picked per clip from the median Haar-cascade face centre over nine samples —
face centre drifts between 767 px and 1017 px across the talk, so a fixed centre
crop would sit off-axis on some speakers.

The 1.78x upscale is real quality loss, but the source is a soft 1.9 Mbps webcam
feed to begin with; the mild unsharp recovers most of the apparent detail.

### Layout `tile`

For the three clips sourced from the screen-share block, where the speaker
exists only as the 477x270 thumbnail.

A 288x240 crop of the thumbnail — centred on the measured face position, x≈237
of 477, and stopping above the Meet name label in the bottom ~30 px — upscaled
3.75x to 1080x900 over a heavily blurred, darkened fill of the same thumbnail.

This replaced a stacked composite that put the shared desktop under the speaker.
The stacked version was built and rejected on inspection: across all three
clips the shared screen is a dark, static IDE. Blurring it for the background
produced near-black mud, and the desktop itself is illegible at any size that
fits beside a face on a phone — the full 1440 px desktop at 1080 px wide puts
editor text at roughly 9 px. `screen_filter()` is still in `render.py` for a
future clip where the screen actually shows something worth reading.

3.75x is the practical zoom ceiling. Filling a true 9:16 frame from this source
would mean cropping about 152x270 and upscaling roughly 7x, which is mush. These
clips carry more surrounding black than the `head` ones as a result; that is a
property of the source, not a setting.

## Captions

Burned in, since shorts are largely watched muted and blog embeds autoplay
silent. Built from Whisper word-level timings (`small.en`, beam 5, VAD-filtered)
into ASS, with the currently spoken word tinted amber so the eye tracks speech.

Chunking targets a phone screen: at most 6 words, ~2.6 s, two balanced lines,
split on pauses over 0.55 s. A chunk is held 0.35 s past its last word but
never into the next chunk — overlapping ASS events stack vertically in libass
and scramble the reading order.

Three details that only showed up on review:

- A chunk of one or two words is merged back into its predecessor. The word cap
  alone can strand a sentence's last word alone on screen, which reads as a
  dropped word rather than an ending.
- Captions never span an internal cut: each source segment is chunked
  separately, so a caption cannot imply two spliced sentences were one.
- Whisper splits hyphenates into two tokens ("pre", "-planning"); a token
  beginning with a hyphen is re-joined without a space.

Individual mis-transcriptions are corrected per clip through `caption_fixes` in
`clips.json`, which targets the word nearest a given timestamp rather than
replacing every occurrence in the talk. Four were needed — see `docs/review.md`.

## Cuts

A clip is a list of source segments, concatenated in one encode (each segment is
a separate fast-seeked input, so nothing decodes from 0). Two clips use an
internal cut: `06` drops an off-hand line about scammers by nationality, and
`07` drops a tangent about running several models in parallel. Both keep the
clip on one idea.

Trim points sit exactly on the target word's start time. Starting *just before*
it pulls in the tail of the preceding filler word when the two are contiguous,
which is audible — that bug shipped in one round and was caught on review.
