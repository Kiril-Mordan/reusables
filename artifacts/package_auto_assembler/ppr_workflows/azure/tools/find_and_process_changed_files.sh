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
    # Include files from the directory and nested subdirectories.
    files=$(git diff --name-only $commit_range -- "$dir" | grep -E "^${dir}.+")
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
    # Process changed file paths to module/package names.
    while IFS= read -r file; do
      [ -z "$file" ] && continue
      file="${file#./}"
      root="${file%%/*}"
      label=""

      case "$root" in
        python_modules)
          if [[ "$file" == python_modules/components/* ]]; then
            remainder="${file#python_modules/components/}"
            candidate_dir="${remainder%%/*}"
            if [[ -f "python_modules/${candidate_dir}.py" ]]; then
              label="${candidate_dir}"
            else
              stripped="${candidate_dir%_deps}"
              if [[ "$stripped" != "$candidate_dir" && -f "python_modules/${stripped}.py" ]]; then
                label="${stripped}"
              else
                while IFS= read -r module_path; do
                  module_name="$(basename "$module_path" .py)"
                  [ -n "$module_name" ] && echo "$module_name" >> /tmp/paa_changed_modules.$$ 
                done < <(find python_modules -maxdepth 1 -type f -name '*.py' | sort)
                continue
              fi
            fi
          else
            base="$(basename "$file")"
            label="${base%.*}"
          fi
          ;;
        example_notebooks|cli|mcp|api_routes|streamlit|drawio)
          base="$(basename "$file")"
          label="${base%.*}"
          ;;
        tests|artifacts|extra_docs|licenses|skills)
          remainder="${file#${root}/}"
          label="${remainder%%/*}"
          ;;
        *)
          base="$(basename "$file")"
          label="${base%.*}"
          ;;
      esac

      label="${label//-/_}"
      if [ -n "$label" ]; then
        echo "$label" >> /tmp/paa_changed_modules.$$
      fi
    done <<< "$changed_files"

    processed_files=$(sort -u /tmp/paa_changed_modules.$$ 2>/dev/null | awk -v dir="$output_directory" -v ext="$extension_to_add" '{print dir "" $0 ext}')
    rm -f /tmp/paa_changed_modules.$$
    echo "Processed files:"
    echo "$processed_files"
    echo "$processed_files" > changed_files
fi
