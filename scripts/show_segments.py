"""Print transcript segments in a time range with exact boundaries."""
import json
import sys

t = json.load(open("build/transcript.json"))
lo, hi = float(sys.argv[1]), float(sys.argv[2])
for s in t:
    if s["end"] > lo and s["start"] < hi:
        m0, s0 = divmod(s["start"], 60)
        print(f"{s['start']:8.2f} -> {s['end']:8.2f}  [{int(m0):02d}:{s0:05.2f}]  {s['text']}")
