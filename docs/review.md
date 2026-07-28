# Gemini review pass

Three rounds of second-opinion review on the rendered shorts, using
`gemini-3.6-flash` via `scripts/review_gemini.py`. The reviewer is given the
finished mp4 — not the edit plan — so it grades what a viewer actually sees:
caption sync, crop, cut seams, audio. Raw output for each round is in
`build/gemini-review-pass1.json`, `-pass2.json`, and `build/gemini-review.json`.

## Scores

| Clip | Round 1 | Round 2 | Final |
|---|---|---|---|
| 01-prompt-injection | not ready | ready | ready |
| 02-blast-radius | not ready | ready | ready |
| 03-one-decision-per-turn | ready | ready | ready |
| 04-dont-build-dev-tools | ready | ready | ready |
| 05-niche-markets | ready | not ready | ready |
| 06-job-boards-are-dead | not ready | ready | ready |
| 07-adversarial-review | ready | not ready | ready |
| 08-planning-beats-agile | not ready | ready | ready |

3/8 → 6/8 → 8/8 publish-ready.

## What the review caught that was real

**A wrong person on screen.** Round 1 reported "a stray frame of a different
participant at 00:00" on `06`. It was worse than that: the first ~1.6 s showed
the host, not Christopher, because Meet had not switched active speaker yet when
he started talking. Fixed by starting the clip after the switch at 2438.4 s,
which also dropped a weak "Yeah, I think that…" opening.

**Four transcription errors in burned-in captions**, all confirmed against the
audio and corrected via `caption_fixes` in `clips.json`:

| Clip | Whisper heard | Actually said |
|---|---|---|
| 01 | free reign | free rein |
| 06 | posted to job online | posted a job online |
| 08 | writing codes | writing code |
| 08 | into the codes | into the code |

**Cold opens on filler.** `01` opened on "So…" plus a nose-rub, `05` on a
dangling "And", `07` on the stumble "I like you can make it", `08` on "And so I
actually". All retrimmed to start on the thesis.

That last set exposed a bug in how I was choosing trim points: I started *just
before* the target word, which pulled in the tail of the preceding filler word
when the two were contiguous. Round 2 caught `05` still opening on "And" and
`07` still opening on "like". Corrected to start exactly at the target word's
start time.

**An orphaned caption.** Round 2 reported the final word of `05` missing. It was
on screen, but stranded alone as a one-word caption ("tools.") after the
six-word cap split the phrase — which reads as a dropped word. `chunk_words` now
merges short trailing chunks back into their predecessor.

## What I checked and did not act on

**"The crop clips the top of the speaker's head"** (`04`, `06`). It does not.
Pulling the top 520 px of the rendered frames shows clear headroom above the
scalp in every sampled frame. Not changed.

**"The speaker says 'it'll', the caption says 'you'll'"** (`07`, 00:50).
Re-transcribing that span with `medium.en` — a larger model than the `small.en`
used for the main pass — also produced "you'll", twice. The original stands.

**"Filler words omitted from captions"** (`01`, `06`). Correct but intended:
Whisper's VAD drops some "you know" / "like" / "And so". Dropping filler makes
captions more readable, which is standard for the format.

**"Giant black bars, crop in so the speaker fills the frame"** (`01`, `02`,
`03`). Not fixable at acceptable quality. Those three clips are sourced from a
screen-share section where the speaker exists only as a 477x270 thumbnail. The
hero crop is already zoomed to 288x240 upscaled 3.75x; filling a true 9:16 frame
would mean cropping ~152x270 and upscaling roughly 7x. The framing score for
this identical layout ranged 2–5 across rounds, which suggests scoring variance
more than a defect.

## Where the reviewer contradicted itself

Round 1 marked `02` not-ready because it opened mid-thought on "The risk of
doing all of that", referencing context outside the clip, and asked for setup. I
added 17 s of setup. Round 3 then marked it not-ready for the opposite reason —
"rambles through setup for 45 seconds before reaching the main thesis."

Both notes point at the same underlying problem from different sides, so the
final cut satisfies neither literally: it opens directly on "the best thing that
you can do is limit the blast radius" and keeps only the two concrete controls,
at 38 s instead of 81 s. The vault and secrets-proxy nuance belongs in the post
body, not in a short.

Treat the scores as directional. They move by a point or two between identical
runs, and `05` and `07` were marked ready in round 1 and not-ready in round 2
without changing in ways that would explain it. The specific, checkable claims —
a wrong face, a misheard word, a cold open on filler — were consistently worth
acting on. The aesthetic scores were not.
