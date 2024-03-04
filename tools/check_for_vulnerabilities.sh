#!/bin/bash

# Directory containing requirements files
requirements_dir="./env_spec"

# Array of exception files to skip
declare -a exception_files=("requirements_dev.txt")

# Function to run pip-audit and check for vulnerabilities
audit_requirements_file() {
    local requirements_file=$1
    local audit_output

    # Run pip-audit with the specified requirements file
    audit_output=$(pip-audit -r "$requirements_file")

    # Check if vulnerabilities are found
    if echo "$audit_output" | grep -q "Vulnerabilities found"; then
        echo "Vulnerabilities found in $requirements_file!"
        echo "$audit_output"
        return 1
    else
        #echo "No known vulnerabilities found"
        return 0
    fi
}

# Install pip-audit if it's not already installed
python -m pip install pip-audit

# Iterate over all requirements files in the specified directory
for file in "$requirements_dir"/requirements_*.txt; do
    # Check if the current file is in the list of exceptions
    skip_file=0
    for exception in "${exception_files[@]}"; do
        if [[ "$file" == *"$exception" ]]; then
            echo "Skipping audit for $file (listed as exception)."
            skip_file=1
            break
        fi
    done

    # If the file is not in the list of exceptions, audit it
    if [[ $skip_file -eq 0 ]]; then
        echo "Auditing requirements in $file..."
        if ! audit_requirements_file "$file"; then
            exit 1 # Exit if vulnerabilities are found
        fi
    fi
done
