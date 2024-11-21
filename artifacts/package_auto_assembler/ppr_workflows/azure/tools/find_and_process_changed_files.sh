#!/bin/bash

# Directories to check, passed as arguments before the last two arguments
directories_to_check=("${@:1:$#-2}")

# Output directory, passed as the second-to-last argument
output_directory="${@: -2:1}"

# File extension to add, passed as the last argument
extension_to_add="${@: -1}"

# Function to check for changes in a given commit range
check_changes() {
  local commit_range=$1
  local changed_files=""
  for dir in "${directories_to_check[@]}"; do
    # Ensure we only match files directly in the specified directory
    files=$(git diff --name-only $commit_range -- $dir | grep -E "^${dir}[^/]+$")
    if [ -n "$files" ]; then
      changed_files+="$files"$'\n'
    fi
  done
  echo "$changed_files"
}

# Checking for changes in the last three commits
changed_files=""
for i in 1 2 3; do
  changed_files=$(check_changes "HEAD~$i..HEAD~$((i-1))")
  if [ -n "$changed_files" ]; then
    break
  fi
  echo "No changes found between HEAD~$i and HEAD~$((i-1))."
done

if [ -z "$changed_files" ]; then
    echo "No changes found in the last three commits."
else
    echo "Changed files:"
    echo "$changed_files"
    # Process files
    processed_files=$(echo "$changed_files" |
                      sed 's/.*\///' |       # Remove directory path
                      sed 's/\.[^.]*$//' |   # Remove file extensions
                      sort | uniq |         # Sort and deduplicate
                      awk -v dir="$output_directory" -v ext="$extension_to_add" '{print dir "" $0 ext}')  # Prepend directory and append extension
    echo "Processed files:"
    echo "$processed_files"
    echo "$processed_files" > changed_files
fi
