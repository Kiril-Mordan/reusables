#!/bin/bash

# Ensure yq is installed
if ! command -v yq &> /dev/null; then
    echo "yq is required to parse the YAML file. Install it first (e.g., 'sudo apt install yq' or 'brew install yq')."
    exit 1
fi

CONFIG_FILE=".paa.config"
MODULE_DIR=$(yq -r '.module_dir' "$CONFIG_FILE")
EXAMPLE_DIR=$(yq -r '.example_notebooks_path' "$CONFIG_FILE")
CLI_DIR=$(yq -r '.cli_dir' "$CONFIG_FILE")
API_ROUTES_DIR=$(yq -r '.api_routes_dir' "$CONFIG_FILE")
STREAMLIT_DIR=$(yq -r '.streamlit_dir' "$CONFIG_FILE")
DRAWIO_DIR=$(yq -r '.drawio_dir' "$CONFIG_FILE")

echo "$MODULE_DIR $EXAMPLE_DIR $CLI_DIR $API_ROUTES_DIR $STREAMLIT_DIR $DRAWIO_DIR"