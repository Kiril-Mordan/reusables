#!/bin/bash

# Directory containing PNG files
PNG_DIR="./docs" # replace with your actual directory path

# Change to the directory with PNG files
cd "${PNG_DIR}"

# Loop through all PNG files in the directory
for PNG_FILE in *.png; do
    # Skip if it's not a file
    if [[ ! -f $PNG_FILE ]]; then
        continue
    fi

    # Name of the HTML file to be created
    HTML_FILE="${PNG_FILE%.png}.html"

    # HTML content
    HTML_CONTENT="
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>${PNG_FILE%.png} Diagram</title>
</head>
<body>
    <h1>${PNG_FILE%.png} Diagram</h1>
    <img src=\"${PNG_FILE}\" alt=\"${PNG_FILE%.png} Diagram\">
</body>
</html>
"

    # Write the HTML content to the HTML file
    echo "${HTML_CONTENT}" > "${HTML_FILE}"
    echo "HTML file created for ${PNG_FILE}: ${HTML_FILE}"
done

echo "All PNG files have been processed."
