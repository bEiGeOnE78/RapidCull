#!/usr/bin/env bash
set -euo pipefail

check_command() {
  local cmd="$1"
  local install_hint="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required system dependency: $cmd"
    echo "Install hint (Ubuntu/Debian): $install_hint"
    exit 1
  fi
}

check_command exiftool "sudo apt-get install -y libimage-exiftool-perl"
check_command ffmpeg "sudo apt-get install -y ffmpeg"

imagemagick_cmd=""
if command -v magick >/dev/null 2>&1; then
  imagemagick_cmd="magick"
elif command -v convert >/dev/null 2>&1; then
  imagemagick_cmd="convert"
else
  echo "Missing required system dependency: ImageMagick (magick/convert)"
  echo "Install hint (Ubuntu/Debian): sudo apt-get install -y imagemagick"
  exit 1
fi

imagemagick_formats="$($imagemagick_cmd -list format 2>/dev/null || true)"
if [[ "$imagemagick_formats" != *"HEIC"* && "$imagemagick_formats" != *"HEIF"* ]]; then
  echo "Missing required ImageMagick HEIF capability (HEIC/HEIF delegate unavailable)."
  echo "Install hint (Ubuntu/Debian): sudo apt-get install -y libheif1 imagemagick"
  echo "If already installed, ensure your ImageMagick build includes HEIF support and retry."
  exit 1
fi

check_command rawtherapee-cli "sudo apt-get install -y rawtherapee"

echo "System dependency verification passed."
