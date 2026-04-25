#!/usr/bin/env bash
# Downloads the Adhan recording (Sheikh Omar Sunbul, Madinah) into this directory.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$DIR/adhan.mp3"
URL='https://archive.org/download/31813MadinahFajrAdhanSheikhSunbul/31-8-13%20Madinah%20Fajr%20Adhan%20Sheikh%20Sunbul.mp3'

if [ -f "$OUT" ]; then
  echo "$OUT already exists ($(du -h "$OUT" | cut -f1)). Delete it first if you want a fresh download."
  exit 0
fi

echo "Downloading Adhan to $OUT ..."
curl -L --fail --progress-bar -o "$OUT" "$URL"
echo "Done. Size: $(du -h "$OUT" | cut -f1)"
