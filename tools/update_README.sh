#!/bin/bash

./tools/update_gh_pages_links.sh
./tools/update_readme_alt_content.sh

cat docs/README_base.md > README.md

echo ' ' >> README.md

cat links.md >> README.md

echo ' ' >> README.md

echo 'Other content can be found [here](./docs/alternative_content.md).' >> README.md

#cat "$output_file" >> README.md

#rm documentation.md