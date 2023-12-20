#!/bin/bash

requirements_directory="env_spec"  # Directory containing requirements_*.txt files
combined_requirements="requirements.txt"

# Temporary file for combined requirements
temp_combined="$requirements_directory/temp_combined_requirements.txt"

# Read each requirements file
for file in "$requirements_directory"/requirements_*.txt; do
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines and comments
        if [[ -z "$line" ]] || [[ "$line" == \#* ]]; then
            continue
        fi

        # Add line to temp_combined file
        echo "$line" >> "$temp_combined"
    done < "$file"
done

# Function to compare versions and keep the highest version
keep_highest_version() {
    awk -F'[=><]' '{
        package=$1;
        version=$2;
        if (version && (!seen[package] || seen[package] < version)) {
            seen[package]=version;
        } else if (!seen[package]) {
            seen[package]="unspecified";
        }
    }
    END {
        for (package in seen) {
            version = seen[package];
            if (version == "unspecified") {
                print package;
            } else {
                print package "==" version;
            }
        }
    }' "$@"
}

# Sort, remove duplicates, and keep the highest version
keep_highest_version "$temp_combined" > "$requirements_directory/$combined_requirements"

# Clean up temporary files
rm "$temp_combined"

echo "Combined requirements file created at $requirements_directory/$combined_requirements"