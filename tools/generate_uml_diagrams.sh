#!/bin/bash

# Directories for PlantUML files and output diagrams
PLANTUML_DIR="./plantuml"
DOCS_DIR="./docs"

# Create the docs directory if it doesn't exist
mkdir -p "${DOCS_DIR}"

# Loop through all .txt files in the PlantUML directory
for file in "${PLANTUML_DIR}"/*.txt; do
    # Skip if it's not a file
    if [[ ! -f $file ]]; then
        continue
    fi

    # Extract the filename without the extension
    filename=$(basename -- "$file")
    filename="${filename%.*}"

    # Generate PNG diagram and save it in the docs directory
    java -jar plantuml.jar -tpng "$file" -o "${DOCS_DIR}"

    # Rename the generated PNG to match the original txt filename
    mv "${DOCS_DIR}/${filename}.png" "${DOCS_DIR}/${filename}.png"
done

echo "All PlantUML .txt files have been processed."
