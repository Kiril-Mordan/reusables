#!/bin/bash

input_dir="drawio"
output_dir=".paa/docs"
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
      max_file=""
      max_size=0
      temp_files=()

      for attempt in {1..3}; do
        temp_file="${output_dir}/${base_name}-${page_name}-temp-${attempt}.${format}"
        xvfb-run -a drawio --export --format "$format" --output "$temp_file" --page-index "$page_index" "$input_file"
        
        # Track temporary files for later deletion
        temp_files+=("$temp_file")
        
        # Check file size and update max_file if this is the largest one
        file_size=$(stat -c%s "$temp_file")
        if (( file_size > max_size )); then
          max_size=$file_size
          max_file=$temp_file
        fi

        sleep 3
      done

      # Move the largest file to the final output and delete other temporary files
      output_file="${output_dir}/${base_name}-${page_name}.${format}"
      mv "$max_file" "$output_file"
      for file in "${temp_files[@]}"; do
        [[ "$file" != "$max_file" ]] && rm -f "$file"
      done

      page_index=$((page_index + 1))
    fi
  done
done
