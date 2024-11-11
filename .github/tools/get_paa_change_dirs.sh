#!/bin/bash

# Ensure yq is installed
if ! command -v yq &> /dev/null; then
    echo "yq is required to parse the YAML file. Install it first (e.g., 'sudo apt install yq' or 'brew install yq')."
    exit 1
fi

CONFIG_FILE=".paa.config"

# Function to remove leading './' and add a trailing slash if missing
sanitize_dir_path() {
    dir_path="$1"
    # Remove leading './' if present
    dir_path="${dir_path#./}"
    # Ensure trailing slash
    [[ "${dir_path: -1}" != "/" ]] && dir_path="${dir_path}/"
    echo "$dir_path"
}

# Read directories from the config file and sanitize them
MODULE_DIR=$(sanitize_dir_path "$(yq -r '.module_dir' "$CONFIG_FILE")")
EXAMPLE_DIR=$(sanitize_dir_path "$(yq -r '.example_notebooks_path' "$CONFIG_FILE")")
CLI_DIR=$(sanitize_dir_path "$(yq -r '.cli_dir' "$CONFIG_FILE")")
API_ROUTES_DIR=$(sanitize_dir_path "$(yq -r '.api_routes_dir' "$CONFIG_FILE")")
STREAMLIT_DIR=$(sanitize_dir_path "$(yq -r '.streamlit_dir' "$CONFIG_FILE")")
DRAWIO_DIR=$(sanitize_dir_path "$(yq -r '.drawio_dir' "$CONFIG_FILE")")

# Output the directory paths with trailing slashes and no leading './'
echo "$MODULE_DIR $EXAMPLE_DIR $CLI_DIR $API_ROUTES_DIR $STREAMLIT_DIR $DRAWIO_DIR"
