#!/bin/bash

# Default threshold score to pass the Pylint check
threshold_score=6

# Parse arguments for module_directory and threshold_score
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --module-directory) module_directory="$2"; shift ;;
        --threshold) threshold_score="$2"; shift ;;
        *) files_to_check+=("$1") ;;  # Treat positional arguments as files to check
    esac
    shift
done

# Ensure module_directory is set if no specific files are provided
if [ -z "$module_directory" ] && [ ${#files_to_check[@]} -eq 0 ]; then
    echo "Error: --module-directory is required if no specific files are provided."
    exit 1
fi

# Function to run Pylint on a Python script and capture the score
function run_pylint() {
    pylint_output=$(pylint "$1")
    pylint_score=$(echo "$pylint_output" | grep -oE 'rated at [0-9]+\.[0-9]+')
    pylint_score=${pylint_score#* at }  # Remove "rated at " prefix
    echo "$pylint_score"
}

# If no specific files are provided, find all Python files in the module directory
if [ ${#files_to_check[@]} -eq 0 ]; then
    files_to_check=($(find "$module_directory" -type f -name "*.py"))
fi

# Loop through specified Python files and check Pylint score
all_pass=true
for script in "${files_to_check[@]}"; do
    # Only apply the module_directory pattern check if no specific files were provided
    if [[ ${#files_to_check[@]} -eq 0 || "$script" =~ $script_pattern ]]; then
        score=$(run_pylint "$script")
        echo "Pylint score for $script is $score"
        if (( $(awk -v score="$score" -v threshold="$threshold_score" 'BEGIN { print (score >= threshold) }') )); then
            all_pass=true
        else
            all_pass=false
            echo "Pylint score for $script is below the threshold."
            exit 1  # Exit immediately with an error message
        fi
    fi
done

# Check if all scripts passed the Pylint check
if $all_pass; then
    echo "All scripts passed the Pylint check!"
    exit 0
fi
