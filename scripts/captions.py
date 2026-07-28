"""Build ASS subtitles with word-level highlighting from Whisper word timings.

Shorts are watched muted more often than not, so captions carry the clip. The
active word is tinted so the eye tracks the speech rather than re-reading the
whole chunk on every redraw.
"""

PLAY_W, PLAY_H = 1080, 1920

# ASS colours are &HAABBGGRR (alpha first, then BGR).
WHITE = "&H00FFFFFF"
ACCENT = "&H0043D6FF"  # amber, BGR order
OUTLINE = "&H00000000"


def _esc(text):
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def chunk_words(words, max_chars=30, max_words=6, max_dur=2.6, gap_split=0.55):
    """Group words into caption chunks sized for a phone screen."""
    chunks, cur = [], []
    for w in words:
        if cur:
            too_long = sum(len(x["w"]) + 1 for x in cur) + len(w["w"]) > max_chars * 2
            too_many = len(cur) >= max_words
            too_slow = w["e"] - cur[0]["s"] > max_dur
            big_gap = w["s"] - cur[-1]["e"] > gap_split
            if too_long or too_many or too_slow or big_gap:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)

    # Pull short trailing chunks back into their predecessor. Splitting on the
    # word cap alone can strand a one-word tail ("tools.") on screen by itself,
    # which reads as a dropped word rather than the end of the sentence.
    merged = []
    for c in chunks:
        if merged and len(c) <= 2:
            prev = merged[-1]
            chars = sum(len(x["w"]) + 1 for x in prev + c) - 1
            span = c[-1]["e"] - prev[0]["s"]
            if len(prev) + len(c) <= max_words + 2 and chars <= max_chars * 2 and span <= max_dur + 1.0:
                merged[-1] = prev + c
                continue
        merged.append(c)
    return merged


def _wrap(tokens, max_chars=30):
    """Split rendered tokens across at most two lines, balancing length."""
    plain = [t[1] for t in tokens]
    if sum(len(p) + 1 for p in plain) - 1 <= max_chars:
        return [tokens]
    best, best_cost = 1, None
    for i in range(1, len(tokens)):
        a = sum(len(p) + 1 for p in plain[:i]) - 1
        b = sum(len(p) + 1 for p in plain[i:]) - 1
        cost = max(a, b) + abs(a - b) * 0.3
        if best_cost is None or cost < best_cost:
            best, best_cost = i, cost
    return [tokens[:best], tokens[best:]]


def remap(words, segments):
    """Project source-timed words onto the concatenated output timeline.

    Words are clipped to their segment, so a word straddling a cut keeps only
    the part that survives the edit.
    """
    groups, offset = [], 0.0
    for s, e in segments:
        g = []
        for w in words:
            if w["e"] > s and w["s"] < e:
                ws, we = max(w["s"], s), min(w["e"], e)
                g.append({"w": w["w"], "s": ws - s + offset, "e": we - s + offset})
        groups.append(g)
        offset += e - s
    return groups, offset


def build_ass(words, segments, title=None, font="DejaVu Sans"):
    """Render an ASS file for a clip built from one or more source segments."""
    groups, clip_end = remap(words, segments)
    clip_start = 0.0

    def ts(t):
        t = max(0.0, t - clip_start)
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {PLAY_W}
PlayResY: {PLAY_H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},72,{WHITE},{WHITE},{OUTLINE},&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,60,60,210,1
Style: Title,{font},50,{WHITE},{WHITE},&H66000000,&H66000000,-1,0,0,0,100,100,0,0,3,14,0,8,70,70,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = []

    if title:
        lines.append(
            f"Dialogue: 0,{ts(clip_start)},{ts(clip_end)},Title,,0,0,0,,{_esc(title)}"
        )

    # Chunk each source segment separately so a caption never spans a cut.
    chunks = [c for g in groups for c in chunk_words(g)]
    for ci, chunk in enumerate(chunks):
        c_start = max(chunk[0]["s"], clip_start)
        # Hold the chunk a beat past the last word, but never into the next one:
        # overlapping events stack vertically in libass and scramble the read.
        hold = chunk[-1]["e"] + 0.35
        if ci + 1 < len(chunks):
            hold = min(hold, chunks[ci + 1][0]["s"])
        c_end = min(hold, clip_end)
        if c_end <= c_start:
            continue
        # One event per active-word window so the highlight advances in place.
        for i, w in enumerate(chunk):
            seg_s = max(c_start, w["s"]) if i else c_start
            seg_e = c_end if i == len(chunk) - 1 else min(chunk[i + 1]["s"], c_end)
            if seg_e <= seg_s:
                continue
            toks = [(j, _esc(x["w"])) for j, x in enumerate(chunk)]
            rows = []
            for row in _wrap(toks):
                line = ""
                for j, t in row:
                    painted = f"{{\\1c{ACCENT}}}{t}{{\\1c{WHITE}}}" if j == i else t
                    # Whisper splits hyphenates into two tokens ("pre",
                    # "-planning"); re-join those without a space.
                    line += painted if (not line or t.startswith("-")) else " " + painted
                rows.append(line)
            lines.append(
                f"Dialogue: 0,{ts(seg_s)},{ts(seg_e)},Caption,,0,0,0,,"
                + "\\N".join(rows)
            )

    return head + "\n".join(lines) + "\n"
