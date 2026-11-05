#!/usr/bin/env bash
# Download the latest Fiji (Linux, bundled JDK) into DEST (default .fiji) unless
# already there. Writes DEST/FIJI_DIR and DEST/FIJI_LAUNCHER for CI steps.
# Used by ci.yml / weekly.yml / release.yml. Linux only.
set -euo pipefail
DEST="${1:-.fiji}"
URL="${FIJI_URL:-https://downloads.imagej.net/fiji/latest/fiji-latest-linux64-jdk.zip}"
mkdir -p "$DEST"
if [ ! -f "$DEST/FIJI_DIR" ]; then
  echo "Downloading $URL"
  curl -fsSL --retry 3 -o "$DEST/fiji.zip" "$URL"
  unzip -q "$DEST/fiji.zip" -d "$DEST"
  rm "$DEST/fiji.zip"
  # The zip's top folder has been called Fiji.app and Fiji over the years.
  dir="$(find "$DEST" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  echo "$(cd "$dir" && pwd)" > "$DEST/FIJI_DIR"
fi
FIJI="$(cat "$DEST/FIJI_DIR")"
for l in fiji-linux-x64 ImageJ-linux64 fiji; do
  if [ -x "$FIJI/$l" ]; then echo "$l" > "$DEST/FIJI_LAUNCHER"; break; fi
done
echo "Fiji at $FIJI, launcher $(cat "$DEST/FIJI_LAUNCHER")"
