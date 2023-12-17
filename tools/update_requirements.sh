#!/bin/bash

# Directory containing your Python modules
modules_directory="python_modules"

# Loop through each module
for file in "$modules_directory"/*.py
do
    module_name=$(basename "$file" .py)  # Extract the module name
    echo "Processing module: $module_name"

    # Run your Python script here
    python3 ./tools/extract_requirements.py "$module_name"
done