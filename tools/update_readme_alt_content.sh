#!/bin/bash

# Define the directory containing your Python modules
module_directory="python_modules"
docs_directory="docs"

# Define the base URL for the GitHub Pages
BASE_URL="https://kiril-mordan.github.io/reusables"



# Create the Markdown documentation file
output_file="docs/alternative_content.md"
> "$output_file"

echo "## Content:" > "$output_file"
echo " " >> "$output_file"
echo " " >> "$output_file"

# Function to extract docstring from a Python script
extract_docstring() {
    local file="$1"
    local docstring=$(python -c "import re; import os; title = os.path.basename('$file').replace('.py','').capitalize().replace('_', ' '); content = open('$file').read(); match = re.search(r'\"\"\"(.*?)\"\"\"', content, re.DOTALL); print(f'{title} \n\n' + match.group(1).strip()) if match else ''")
    echo "$docstring"
}

# Find Python files and generate documentation
find "$module_directory" -type f -name "*.py" | while read -r file; do
    module_name=$(basename "$file" .py)
    docstring=$(extract_docstring "$file")

    # Construct the URL
    url="${BASE_URL}/${module_name}"

    if ! curl --head --silent --fail "$url" > /dev/null; then

        if [ -n "$docstring" ]; then
            module_path="python_modules/$module_name.py"
            module_link="[module](../$module_path)"

            # Check if notebook with the same name exists
            notebook_path="$docs_directory/$module_name.md"
            notebook_link=""
            if [ -f "$notebook_path" ]; then
                notebook_link=" | [usage](../$notebook_path)"
            fi

            # Check if a PlantUML diagram with a specific naming convention exists
            diagram_path="${docs_directory}/${module_name}_plantuml.png"
            diagram_link=""
            if [ -f "$diagram_path" ]; then
                diagram_link=" | [plantuml](../$diagram_path)"
            fi

            # Check if drawio diagram with additional text between module name and .png exists, excluding _plantuml.png files
            drawio_diagram_paths=$(find "$docs_directory" -type f -name "${module_name}*.png" | grep -v "_plantuml.png")
            drawio_diagram_link=""
            for drawio_diagram_path in $drawio_diagram_paths; do
                # Extract just the filename from the path
                drawio_diagram_filename="${drawio_diagram_path##*/}"
                # Exclude _plantuml.png files explicitly, just in case
                if [[ ! "$drawio_diagram_filename" =~ _plantuml\.png$ ]]; then
                    # Generate the link. Adjust the URL if you store your documentation in a different structure on the web
                    diagram_identifier=$(echo "$drawio_diagram_filename" | sed "s/${module_name}_\?\(.*\)\.png/\1/")
                    drawio_diagram_link+=" | [drawio: $diagram_identifier](../$drawio_diagram_path)"
                fi
            done

            # Check if release notes with the same name exist
            release_notes_path="release_notes/$module_name.md"
            release_notes_link=""
            if [ -f "$release_notes_path" ]; then
                release_notes_link=" | [release notes](../$release_notes_path)"
            fi

            # Check if pypi module exists
            pypi_module_link="https://pypi.org/project/${module_name//_/-}/"
            pypi_link=""
            if curl -s --head  --request GET "$pypi_module_link" | grep "200 " > /dev/null; then
                pypi_link=" | [![PyPiVersion](https://img.shields.io/pypi/v/${module_name//_/-})](https://pypi.org/project/${module_name//_/-}/)"
            fi

            # Append links and docstring to the output file
            echo "$module_link$notebook_link$diagram_link$drawio_diagram_link$release_notes_link$pypi_link - $docstring" >> "$output_file"
            echo "" >> "$output_file"
        fi
    fi
done

echo "Documentation generated in $output_file"