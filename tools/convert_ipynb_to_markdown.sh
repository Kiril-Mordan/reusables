#!/bin/bash

# Function to convert a Jupyter notebook to markdown
convert_to_markdown() {
  local notebook_file="$1"
  local output_dir="$2"

  # Get the directory path of the notebook file
  local notebook_dir="$(dirname "$notebook_file")"

  # Get the relative path of the notebook directory
  local relative_dir="${notebook_dir#$root_dir}"

  # # Check if the notebook file is 'parameterframe' module
  # if [[ "$notebook_file" == *"parameterframe"* || "$notebook_file" == *"package_auto_assembler"* ]]; then
  #   echo "Skipping execution for module: $notebook_file"
  #   jupyter nbconvert --to markdown "$notebook_file" --output-dir="$output_dir"
  #   return
  # fi

  # # Convert the notebook to markdown and save it in the output directory
  # jupyter nbconvert --to markdown --execute --ExecutePreprocessor.kernel_name=python3 "$notebook_file" --output-dir="$output_dir"
  jupyter nbconvert --to markdown --ExecutePreprocessor.kernel_name=python3 "$notebook_file" --output-dir="$output_dir"
}

# Specify the root directory to start the conversion
root_dir="example_notebooks/"
output_directory="docs/"

# If arguments are provided, process each; otherwise, process all modules in directory
if [ $# -gt 0 ]; then
    for module_file in "$@"; do
        convert_to_markdown "$module_file" "$output_directory"
    done
fi
# else
#     for module_file in "$root_dir"/*.ipynb; do
#         convert_to_markdown "$module_file"
#     done
# fi
