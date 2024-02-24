#!/bin/bash

# Directories for PlantUML files and output diagrams
PLANTUML_DIR="./plantuml"
DOCS_DIR="./docs"

# Loop through all .txt files in the PlantUML directory
for file in "${PLANTUML_DIR}"/*.txt; do
    # Skip if it's not a file
    if [[ ! -f $file ]]; then
        continue
    fi

    # Extract the filename without the extension
    filename=$(basename -- "$file")
    filename="${filename%.*}"

    # Generate PNG diagram
    java -jar plantuml.jar -tpng "$file"

    # Move the generated PNG to the docs directory
    # Assuming PlantUML creates the PNG in the same directory as the .txt file
    mv "${PLANTUML_DIR}/${filename}_plantuml.png" "${DOCS_DIR}/"

done

echo "All PlantUML .txt files have been processed."
