#!/bin/bash

CONFIG_FILE=".paa.config"
PY_FILES_DIR=$(grep 'module_dir:' "$CONFIG_FILE" | sed -E 's/^ *module_dir: *//')
# Directory containing the .yml feed files
YML_DIR=".azure/feeds"
RN_DIR=".paa/release_notes"

# Function to get feeds for a Python package
get_feeds_for_package() {
    local package_name=$1
    local organization=$2

    # Construct payload for the package name
    payload=$(cat <<EOF
{
  "\$orderBy": null,
  "\$top": 100,
  "\$skip": 0,
  "searchText": "$package_name",
  "filters": {
    "ProtocolType": "PyPI"
  }
}
EOF
)
    # Package Search API URL
    API_URL="https://almsearch.dev.azure.com/$organization/_apis/search/packagesearchresults?api-version=7.0"

    # Perform POST request
    response=$(curl -s -u ":$AZURE_PAT" -X POST \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "$API_URL" || echo "{}")

    # Extract feedName and latestVersion pairs
    echo "$response" | grep -oE '"feedName":"[^"]*"|\"latestVersion\":\"[^\"]*\"' \
        | sed -E 's/"feedName":"([^"]*)"/feedName:\1/;s/"latestVersion":"([^"]*)"/latestVersion:\1/'
}

# Function to generate Markdown links for a package
generate_package_links() {
    local package_name=$1
    local links=()

    local feed_colors_file="/tmp/feed_colors.txt"  # Temporary file to store feed-to-color mapping

    # Ensure the file exists
    [[ -f "$feed_colors_file" ]] || touch "$feed_colors_file"

    # Function to get or generate a color for a feed
    get_feed_color() {
        local feed_name=$1
        local existing_color

        # Check if a color already exists for the feed
        existing_color=$(grep "^$feed_name " "$feed_colors_file" | awk '{print $2}')
        if [[ -n "$existing_color" ]]; then
            echo "$existing_color"
        else
            # Generate a random color if not already assigned
            local new_color=$(printf "%06X" $((RANDOM * RANDOM % 0xFFFFFF)))
            echo "$feed_name $new_color" >> "$feed_colors_file"
            echo "$new_color"
        fi
    }
    
    for yml_file in "$YML_DIR"/*.yml; do

        # Extract feed_name and feed_url from the .yml file
        feed_name=$(grep 'feed_name:' "$yml_file" | sed -E 's/^ *feed_name: *//')
        organization=$(grep 'organization:' "$yml_file" | sed -E 's/^ *organization: *//')
        project_guid=$(grep 'project_guid:' "$yml_file" | sed -E 's/^ *project_guid: *//')

        feed_url="https://dev.azure.com/$organization/$project_guid/_artifacts/feed/$feed_name/"    

        # Get the list of feeds from the API response
        feeds=$(get_feeds_for_package "$package_name" "$organization")

        # Check if the feed_name exists in the API response
        if echo "$feeds" | grep -q "$feed_name"; then

            # Get color for feed
            feed_color=$(get_feed_color "$feed_name")

            # Extract the latestVersion for the matching feed
            latest_version=$(echo "$feeds" | awk -v feed="$feed_name" '
$1 == "feedName:" feed {getline; if ($1 ~ "latestVersion:") {split($1, a, ":"); print a[2]}}')


            # Construct package link using feed_url
            package_url="${feed_url}/PyPI/$package_name"
            
            # Prepare names
            display_name=$(echo "${package_name//_/-}")
            package_rn=$(echo $package_name |  sed 's/-/_/g').md

            # Make badges
            package_badge="https://img.shields.io/static/v1?label=&message=${display_name}&color=lightblue"
            azure_badge="https://img.shields.io/static/v1?label=&message=${feed_name}&color=$feed_color"
            version_badge="https://img.shields.io/static/v1?label=&message=${latest_version}&color=red"

            links+=("- [![Package Name]($package_badge)]($RN_DIR/$package_rn) [![Latest Version]($version_badge)]($package_url) [![Azure Feed]($azure_badge)]($feed_url)")
        fi
    done

    # Print the final list of links
    if [ ${#links[@]} -gt 0 ]; then
        printf "%s\n" "${links[@]}"
    else
        echo ""
    fi
}


for file in "$PY_FILES_DIR"/*.py; do
    if [ -f "$file" ]; then
        # Extract package name
        package_name=$(basename "$file" .py | sed 's/_/-/g')
        generate_package_links "$package_name"
    fi
done
