#!/bin/bash

# Function to process a single module
process_module() {
    local module_file=$1
    local module_name=$(basename "$module_file" .py)

    echo "Assebling package for module: $module_name"

    paa make-package "$module_name" --config .paa.config
}

for module_file in "$@"; do
        process_module "$module_file"
done
