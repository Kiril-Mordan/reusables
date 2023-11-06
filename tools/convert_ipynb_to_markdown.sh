#!/bin/bash

# Function to convert a Jupyter notebook to markdown
convert_to_markdown() {
  local notebook_file="$1"
  local output_dir="$2"

  # Get the directory path of the notebook file
  local notebook_dir="$(dirname "$notebook_file")"

  # Get the relative path of the notebook directory
  local relative_dir="${notebook_dir#$root_dir}"

  # Convert the notebook to markdown and save it in the output directory
  jupyter nbconvert --to markdown --execute "$notebook_file" --output-dir="$output_directory"
}

# Recursive function to find and convert .ipynb files in a directory
convert_ipynb_files() {
  local dir="$1"

  # Loop through all files and directories in the current directory
  for item in "$dir"/*; do
    if [[ -d "$item" ]]; then
      # If it's a directory, recursively call the function
      convert_ipynb_files "$item"
    elif [[ -f "$item" && "${item##*.}" == "ipynb" ]]; then
      # If it's a .ipynb file, convert it to markdown
      convert_to_markdown "$item"
    fi
  done
}

# Specify the root directory to start the conversion
root_dir="example_notebooks/"
output_directory="docs/"

# Call the function to convert .ipynb files
convert_ipynb_files "$root_dir"