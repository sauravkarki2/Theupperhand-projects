#!/usr/bin/env bash
# Joins the silent render with the synthesized soundtrack, normalized to -14 LUFS / -1 dBTP.
set -euo pipefail
cd "$(dirname "$0")/.."
FFMPEG="${FFMPEG:-ffmpeg}"
"$FFMPEG" -y -loglevel error -i out/flownavy_showreel_silent.mp4 -i out/soundtrack.wav \
  -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1:LRA=11,aresample=48000" -c:a aac -b:a 320k \
  -shortest -movflags +faststart out/flownavy_showreel.mp4
echo "wrote out/flownavy_showreel.mp4"
