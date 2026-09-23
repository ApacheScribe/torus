# The Torus, from a Flat Plane (3b1b-style)

960x540 @ 24fps, Pillow wireframe + ffmpeg + narration (xAI TTS).

## Story (one step per sentence)
Cartesian plane -> pick a rectangle -> glue left+right (cylinder) ->
glue top+bottom (torus) -> grid becomes a field of circles -> the map -> recap.

## Frame-exact audio sync (the smart part)
1. Drop the narration at `assets/narr.mp3`.
2. `sh scripts/render.sh` runs `scripts/sync.py`:
   - `ffmpeg silencedetect` finds the natural silence gaps between sentences,
   - sentence starts become timeline boundaries,
   - each boundary is quantized to a frame: `frame = round(t * 24)`,
   - total video frames = `floor(audio_duration * 24)` so video never outlasts audio,
   - `-shortest` on the mux guards the final frame.
3. `torus.py` re-renders with those boundaries: every morph, camera move and
   label fade is a smoothstep with zero-velocity joints, so steps feel
   connected, not chopped. No narration = silent 26s preview with default
   timing (re-render when the mp3 arrives - timing is replaced entirely).

## Pipeline
- `scripts/torus.py` - frame renderer (reads assets/timeline.json if present)
- `scripts/sync.py` - audio analysis -> timeline.json
- `scripts/gen_char.py` + `scripts/gen_overlay2.py` - text overlays
  (glyph-by-glyph subprocess rendering; sandbox kills multi-glyph text
  processes, ~7 glyphs/process is the current limit, so 1 glyph/process)
- `scripts/render.sh` - sync -> chunked render -> mux

## Sandbox gotchas (same as y=mx+c)
random process kills (chunked frames + per-glyph text), flaky workspace
mount (build in /tmp, copy results over), no matplotlib.

## Reproduce
sh scripts/render.sh    # with assets/narr.mp3 or without (silent preview)

## Cloud render (GitHub Actions) — no sandbox fighting
The heavy lifting (624 frames + mux) runs on a real 2-core Linux runner, not iSH.
1. Create a repo (or paste a classic PAT with `repo` scope and it's auto-created).
2. `GH_TOKEN=<pat> sh ci.sh <owner/repo>` — pushes scripts + assets (add
   `assets/narr.mp3` first if you have the narration), waits for the run,
   then pulls the committed mp4 back into this folder.
Rendering is split across 4 parallel jobs (156 frames each) + 1 mux job.
The workflow commits the mp4 + timeline.json back to the repo, so pulling
the branch is all you need to get the result. Push trigger ignores
`*.mp4` and `timeline.json` so the commit-back never re-triggers a run.