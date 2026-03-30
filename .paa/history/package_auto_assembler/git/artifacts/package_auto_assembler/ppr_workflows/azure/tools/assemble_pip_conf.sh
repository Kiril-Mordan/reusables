#!/bin/bash

# Ensure the environment variable for the token is set
if [ -z "$TWINE_PASSWORD" ]; then
  echo "Error: The environment variable TWINE_PASSWORD is not set."
  exit 1
fi

# Ensure the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <organization> <feed_name> <project_guid>"
  exit 1
fi

# Retrieve the arguments
organization="$1"
feed_name="$2"
project_guid="$3"

# Construct the URL
url="https://pkgs.dev.azure.com/$organization/$project_guid/_packaging/$feed_name/pypi/simple/"

# Create the pip.conf file
mkdir -p ~/.config/pip
output_path=~/.config/pip/pip.conf

# Write to the pip.conf file
echo "[global]" > "$output_path"
full_url=$(echo "$url" | sed "s|https://|https://${TWINE_PASSWORD}@|")
echo "extra-index-url=$full_url" >> "$output_path"

echo "pip.conf has been created at $output_path"
