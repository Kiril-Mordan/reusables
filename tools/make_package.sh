#!/bin/bash

# Directory containing your Python modules
modules_directory="python_modules"

# Create empty setup directory
mkdir setup_dir

# Function to process a single module
process_module() {
    local module_file=$1
    local module_name=$(basename "$module_file" .py)

    echo "Preparing dir structure for module: $module_name"

    # flushing setup directory
    rm -r setup_dir
    mkdir setup_dir
    # coping module to setup direcotry
    cp "$modules_directory/$module_name" setup_dir/.
    # creating temp __init__.py file
    echo "from .$module_name import *" > setup_dir/__init__.py

    echo "Preparing setup.py file for module: $module_name"
    python3 ./tools/prep_setup.py "$module_name"
}

make_package(){
    python setup_dir/setup.py sdist bdist_wheel
}


for module_file in "$@"; do
        process_module "$module_file"
done
