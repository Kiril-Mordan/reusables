#!/bin/bash

# Check package name
if [ "$#" -ne 1 ]; then
    echo "No package name provided"
    exit 1
fi

PACKAGE_NAME=$(basename "$1" .py)

# Path to env_spec files
MAPPING_FILE="env_spec/package_mapping.json"
VERSIONS_FILE="env_spec/lsts_package_versions.yml"

# Use jq to attempt to retrieve the mapping value
#MAPPED_VALUE=$(jq -r --arg k "$PACKAGE_NAME" '.[$k]' "$MAPPING_FILE")
MAPPED_VALUE="$PACKAGE_NAME"

# Check if the jq command found a mapping (i.e., the result is not null)
if [ "$MAPPED_VALUE" != "null" ]; then
    # If a mapping was found, update PACKAGE_NAME
    PACKAGE_NAME="$MAPPED_VALUE"
fi


# Get package version from recorded versions
VERSION=$(grep "^${PACKAGE_NAME}:" $VERSIONS_FILE | awk '{print $2}')

if [ -z "$VERSION" ]; then
    echo "$PACKAGE_NAME Version not found"
    exit 1
else
    echo $VERSION
fi