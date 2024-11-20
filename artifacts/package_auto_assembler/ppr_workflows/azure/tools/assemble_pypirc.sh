#!/bin/bash

# Directory containing the .yml files
yml_directory=".azure/feeds"
output_file=".pypirc"

# Initialize .pypirc content
echo "[distutils]" > $output_file
echo "Index-servers =" >> $output_file

# Loop through each .yml file in the directory
for yml_file in "$yml_directory"/*.yml; do
    # Extract feed_name from the .yml file
    feed_name=$(grep 'feed_name:' $yml_file | awk '{print $2}')
    
    # Add feed_name to Index-servers
    echo "  $feed_name" >> $output_file
done

# Add repository information for each feed
for yml_file in "$yml_directory"/*.yml; do
    # Extract feed_name and repository_index again
    feed_name=$(grep 'feed_name:' $yml_file | awk '{print $2}')
    organization_name=$(grep 'organization:' $yml_file | awk '{print $2}')
    project_name=$(grep 'project:' $yml_file | awk '{print $2}')
    repository_index="https://pkgs.dev.azure.com/$organization_name/$project_name/_packaging/$feed_name/pypi/upload/"

    # Add repository details to .pypirc
    echo "" >> $output_file
    echo "[$feed_name]" >> $output_file
    echo "Repository = $repository_index" >> $output_file
done

echo ".pypirc file created successfully."