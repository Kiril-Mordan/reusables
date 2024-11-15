#!/bin/bash

# Ensure the environment variable for the token is set
if [ -z "$TWINE_PASSWORD" ]; then
  echo "Error: The environment variable TWINE_PASSWORD is not set."
  exit 1
fi

# Ensure URLs are provided as an argument
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 \"<url1> <url2> ...\""
  exit 1
fi

# Retrieve the URLs from the argument
urls="$1"

# Create the pip.conf file
output_file="pip.conf"
mkdir -p ~/.config/pip
output_path=~/.config/pip/$output_file

# Start with the [global] section
echo "[global]" > "$output_path"

# Process each URL in the argument string
for url in $urls; do
  # Ensure URL is not empty
  if [ ! -z "$url" ]; then
    # Insert the PAT into the URL
    full_url=$(echo "$url" | sed "s|https://|https://${TWINE_PASSWORD}@|")
    echo "extra-index-url=$full_url" >> "$output_path"
  fi
done

echo "pip.conf has been created at $output_path"
