#!/bin/bash

# Exit immediately on error
set -e

# Function to run Pylint on a Python script and capture the score
function run_pylint() {
    pylint_output=$(pylint "$1")
    pylint_score=$(echo "$pylint_output" | grep -oE 'rated at [0-9]+\.[0-9]+')
    pylint_score=${pylint_score#* at }  # Remove "rated at " prefix
    echo "$pylint_score"
}

# Define the directory containing your Python modules
module_directory="python_modules"

# Regular expression pattern to match Python script files
script_pattern="python_modules/.*\.py"

# Threshold score to pass the Pylint check
threshold_score=7.8

# Loop through Python files that match the pattern and check Pylint score
all_pass=true
find "$module_directory" -type f -name "*.py" | while read -r script; do
    if [[ "$script" =~ $script_pattern ]]; then
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
