#!/bin/bash

# Function to process a single module
process_module() {
    local module_file=$1
    local module_name=$(basename "$module_file" .py)

    echo "Assebling package for module: $module_name"

    python3 ./tools/auto_assemble_package.py "$module_name"
}

for module_file in "$@"; do
        process_module "$module_file"
done
