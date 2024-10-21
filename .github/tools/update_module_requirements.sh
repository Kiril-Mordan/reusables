#!/bin/bash

# Directory containing your Python modules
modules_directory="python_modules"

# Function to process a single module
process_module() {
    local module_file=$1
    local module_name=$(basename "$module_file")
    echo "Processing module: $module_name"
    paa test-install "$module_name"
    paa show-module-requirements "$module_name" > ".paa/requirements/requirements_$module_name.txt"
    
    #python3 ./tools/extract_requirements.py "$module_name"
}

# If arguments are provided, process each; otherwise, process all modules in directory
if [ $# -gt 0 ]; then
    for module_file in "$@"; do
        process_module "$module_file"
    done
else
    for module_file in "$modules_directory"/*.py; do
        process_module "$module_file"
    done
fi

