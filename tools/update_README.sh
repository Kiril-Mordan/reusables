#!/bin/bash

# Define the directory containing your Python modules
module_directory="python_modules"
docs_directory="docs"

# Create the Markdown documentation file
output_file="documentation.md"
> "$output_file"

# Function to extract docstring from a Python script
extract_docstring() {
    local file="$1"
    local docstring=$(python -c "import re; content = open('$file').read(); match = re.search(r'\"\"\"(.*?)\"\"\"', content, re.DOTALL); print(match.group(1).strip()) if match else ''")
    echo "$docstring"
}

# Find Python files and generate documentation
find "$module_directory" -type f -name "*.py" | while read -r file; do
    module_name=$(basename "$file" .py)
    docstring=$(extract_docstring "$file")

    if [ -n "$docstring" ]; then
        module_path="python_modules/$module_name.py"
        module_link="[module]($module_path)"

        # Check if notebook with the same name exists
        notebook_path="$docs_directory/$module_name.md"
        notebook_link=""
        if [ -f "$notebook_path" ]; then
            notebook_link=" | [usage]($notebook_path)"
        fi

        # Check if diagram with the same name exists
        diagram_path="$docs_directory/$module_name.png"
        diagram_link=""
        if [ -f "$diagram_path" ]; then
            diagram_link=" | [diagram]($diagram_path)"
        fi

        # Check if pypi module exists
        pypi_module_link="https://pypi.org/project/${module_name//_/-}/"
        pypi_link=""
        if curl -s --head  --request GET "$pypi_module_link" | grep "200 " > /dev/null; then
            pypi_link=" | [pypi]($pypi_module_link)"
        fi

        # Append links and docstring to the output file
        echo "$module_link$notebook_link$diagram_link$pypi_link - $docstring" >> "$output_file"
        echo "" >> "$output_file"
    fi
done

echo "Documentation generated in $output_file"

cat docs/README_base.md > README.md

echo ' ' >> README.md

cat "$output_file" >> README.md

rm documentation.md