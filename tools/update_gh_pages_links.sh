#!/bin/bash

# Define the base URL for the GitHub Pages
BASE_URL="https://kiril-mordan.github.io/reusables"

# Directory containing the .py files
PY_FILES_DIR="python_modules"

# Create or clear the output file
OUTPUT_FILE="links.md"
> "$OUTPUT_FILE"

echo "## Documentation" > "$OUTPUT_FILE"
echo " " >> "$OUTPUT_FILE"
echo " " >> "$OUTPUT_FILE"
echo "Links to the extended documentation of packaged modules, available through gh-pages:" >> "$OUTPUT_FILE"
echo " " >> "$OUTPUT_FILE"

# Check if the directory exists
if [ ! -d "$PY_FILES_DIR" ]; then
    echo "Directory $PY_FILES_DIR does not exist."
    exit 1
fi

# Iterate over each .py file in the specified directory
for file in "$PY_FILES_DIR"/*.py;
do
    # Check if there are no .py files in the directory
    if [ ! -e "$file" ]; then
        echo "No .py files found in the directory."
        exit 1
    fi

    # Extract the base name of the file (without extension)
    base_name=$(basename "$file" .py)

    # Construct the URL
    url="${BASE_URL}/${base_name}"

    # Check if the URL exists
    if curl --head --silent --fail "$url" > /dev/null; then

        # Replace underscores with dashes and capitalize each word
        display_name=$(echo "${base_name//_/-}" | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1')

        # Append the URL to the output file if it exists
        echo "- [\`${display_name}\`]($url)" >> "$OUTPUT_FILE"
    fi
done

echo "Links have been written to $OUTPUT_FILE"
