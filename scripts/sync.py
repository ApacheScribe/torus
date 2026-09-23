#!/usr/bin/env python3
"""Smart audio->frame sync: detect natural sentence pauses in the narration
with ffmpeg silencedetect, emit boundaries as frame numbers (round(t*FPS)).
Writes assets/timeline.json next to the mp3.
Usage: sync.py <narration.mp3> [noise_dB] [min_gap_s]
"""
import subprocess, json, sys, os, re

mp3 = sys.argv[1]
noise = sys.argv[2] if len(sys.argv) > 2 else "-35"
gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.18
FPS = 24
EXPECT = 6          # sentence starts after t=0 (steps: rect, cyl, tor, field, map, recap)

base = os.path.dirname(os.path.abspath(mp3))
out = os.path.join(base, "timeline.json")

d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "csv=p=0", mp3], capture_output=True, text=True)
dur = float(d.stdout.strip())

r = subprocess.run(["ffmpeg", "-i", mp3, "-af", f"silencedetect=noise={noise}dB:d={gap}",
                    "-f", "null", "-"], capture_output=True, text=True)
ends = sorted(set(float(m) for m in re.findall(r"silence_end: ([0-9.]+)", r.stderr)))
starts = [e for e in ends if 0.3 < e < dur - 0.3]
warn = None
if len(starts) != EXPECT:
    warn = f"silence gaps found={len(starts)}, expected {EXPECT} -> using proportional split"
    starts = [dur * i / EXPECT for i in range(1, EXPECT + 1)]

timeline = {"boundaries": starts, "duration": dur, "fps": FPS}
json.dump(timeline, open(out, "w"))
frames = [round(s * FPS) for s in starts]
print(f"duration={dur:.3f}s  total_frames={int(dur*FPS)}  -> {out}")
print(f"boundaries(s)={[round(s,2) for s in starts]}")
print(f"boundaries(fr)={frames}")
if warn: print("WARN:", warn)