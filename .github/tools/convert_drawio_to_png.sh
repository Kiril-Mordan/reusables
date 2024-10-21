#!/bin/bash

input_dir="drawio"
output_dir="docs"
format="png"

# Ensure output directory exists
mkdir -p "$output_dir"

# Find all .drawio files in the input directory
find "$input_dir" -name '*.drawio' | while read -r input_file; do
  base_name=$(basename "$input_file" .drawio)

  # Extract page names from the .drawio file
  page_names=$(xmllint --xpath '//diagram/@name' "$input_file" | sed 's/name="\([^"]*\)"/\1\n/g')

  page_index=0
  echo "$page_names" | while read -r page_name; do
    if [ -n "$page_name" ]; then
      output_file="${output_dir}/${base_name}-${page_name}.${format}"
      sleep 3
      xvfb-run -a drawio --export --format png --output "$output_file" --page-index "$page_index" "$input_file"
      page_index=$((page_index + 1))
    fi
  done
done
