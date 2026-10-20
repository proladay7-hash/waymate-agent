#!/bin/bash
set -e

MODEL_DIR="/models/blobs"
MODEL_FILE="$MODEL_DIR/sha256-4f659a1e86d7f5a33c389f7991e7224b7ee6ad0358b53437d54c02d2e1b1118d" # Example file
MODEL_URL="link to download models.zip"
MODEL_ZIP="/models/models.zip"
MIN_SIZE=1200000000

# Check if model already exists
if [ -f "$MODEL_FILE" ]; then
  echo "Model already exists, skipping download."
  exit 0
fi

mkdir -p /models

echo "Downloading models.zip from $MODEL_URL..."
curl -L --fail --retry 5 --retry-delay 10 "$MODEL_URL" -o "$MODEL_ZIP"

# Wait for the file to finish downloading and check size
if [ ! -f "$MODEL_ZIP" ]; then
  echo "Download failed: $MODEL_ZIP not found."
  exit 1
fi

FILESIZE=$(stat -c%s "$MODEL_ZIP")
if [ "$FILESIZE" -lt "$MIN_SIZE" ]; then
  echo "Download failed or incomplete: $MODEL_ZIP is only $FILESIZE bytes (expected > $MIN_SIZE)"
  exit 1
fi

echo "Download complete and verified ($FILESIZE bytes). Unzipping..."
unzip -o "$MODEL_ZIP" -d /models/temp

# Move files as before...
if [ -d "/models/temp/models" ]; then
  echo "Moving files from nested structure..."
  mv /models/temp/models/* /models/ 2>/dev/null || true
  rmdir /models/temp/models 2>/dev/null || true
  rmdir /models/temp 2>/dev/null || true
else
  echo "No nested structure found, moving files directly..."
  mv /models/temp/* /models/ 2>/dev/null || true
  rmdir /models/temp 2>/dev/null || true
fi

rm "$MODEL_ZIP"
echo "Done." 