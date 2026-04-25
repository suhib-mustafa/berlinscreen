#!/usr/bin/env bash
# Downloads the Adhan recording (Sheikh Hussein Al-Surayhi, Madinah, Asr).
# This is the regular non-Fajr Adhan, used for Dhuhr/Asr/Maghrib/Isha.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$DIR/adhan.mp3"
URL="https://archive.org/download/BeautifulMadinahAdhanAlAsr15thJan15BySHeikhSurayhi/Beautiful%20Madinah%20Adhan%20Al-Asr%2015th%20Jan%20'15%20by%20SHeikh%20Surayhi.mp3"

if [ -f "$OUT" ]; then
  echo "$OUT already exists ($(du -h "$OUT" | cut -f1)). Delete it first if you want a fresh download."
  exit 0
fi

echo "Downloading Adhan to $OUT ..."
curl -L --fail --progress-bar -o "$OUT" "$URL"
echo "Done. Size: $(du -h "$OUT" | cut -f1)"
