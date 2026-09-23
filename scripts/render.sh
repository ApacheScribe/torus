#!/bin/sh
# Torus video pipeline. Place narr.mp3 in assets/ for a frame-exact audio-synced render.
cd "$(dirname "$0")/.."
ROOT=$(pwd)
TF=/tmp/tb_frames
rm -rf "$TF"; mkdir -p "$TF"

if [ -f "$ROOT/assets/narr.mp3" ]; then
  echo "[sync] analyzing narration..."
  python3 "$ROOT/scripts/sync.py" "$ROOT/assets/narr.mp3" || exit 1
else
  echo "[sync] no assets/narr.mp3 - using 26s default timeline (silent preview)"
  rm -f "$ROOT/assets/timeline.json"
fi

echo "[render] frames..."
for c in 0 1 2 3; do
  s=$((c*156)); e=$((s+156))
  ok=0
  for try in 1 2 3 4; do
    python3 "$ROOT/scripts/torus.py" "$s" "$e" "$TF" && { ok=1; break; }
    echo "  chunk $c retry $try"; sleep 1
  done
  [ $ok -eq 1 ] || { echo "chunk $c failed"; exit 1; }
done

if [ -f "$ROOT/assets/narr.mp3" ]; then
  echo "[mux] video + narration..."
  ffmpeg -y -framerate 24 -i "$TF/f%04d.ppm" -i "$ROOT/assets/narr.mp3" \
    -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k \
    -shortest -movflags +faststart "$ROOT/y_torus_from_plane.mp4"
else
  echo "[mux] silent preview..."
  ffmpeg -y -framerate 24 -i "$TF/f%04d.ppm" -c:v libx264 -preset fast -crf 20 \
    -pix_fmt yuv420p "$ROOT/y_torus_from_plane_preview.mp4"
fi
echo "done -> $ROOT"