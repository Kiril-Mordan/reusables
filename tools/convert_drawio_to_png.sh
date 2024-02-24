#!/bin/bash

# Check if the operating system is macOS
if [[ "$(uname)" == "Darwin" ]]; then
    shopt -s expand_aliases
    alias drawio='/Applications/draw.io.app/Contents/MacOS/draw.io'
fi


SOURCE_DIR="./drawio" # Path to the directory containing .drawio files
TARGET_DIR="./docs" # Path to the directory where .png files should be saved

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Loop through all .drawio files in the source directory
for file in "$SOURCE_DIR"/*.drawio; do
    filename=$(basename "$file" .drawio)
    # Use the draw.io CLI to convert each file to PNG
    drawio --no-sandbox --disable-gpu -x -f png -o "$TARGET_DIR/$filename.drawio.png" "$file"
done
