#!/bin/bash

# Specify the root directory to start the conversion
root_dir="example_notebooks/"
output_directory="docs/"

# Function to convert a Jupyter notebook to markdown
convert_to_markdown() {
  local notebook_file="$1"
  local output_dir="$2"

  # Get the directory path of the notebook file
  local notebook_dir="$(dirname "$notebook_file")"

  # Get the relative path of the notebook directory
  local relative_dir="${notebook_dir#$root_dir}"

  # # Convert the notebook to markdown and save it in the output directory
  # jupyter nbconvert --to markdown --execute --ExecutePreprocessor.kernel_name=python3 "$notebook_file" --output-dir="$output_dir"
  jupyter nbconvert --to markdown --ExecutePreprocessor.kernel_name=python3 "$notebook_file" --output-dir="$output_dir"
}

# If arguments are provided, process each; otherwise, process all modules in directory
if [ $# -gt 0 ]; then
    for module_file in "$@"; do
        convert_to_markdown "$module_file" "$output_directory"
    done
fi