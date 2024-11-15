#!/bin/bash
chmod +x .azure/tools/update_aasf_links.sh
cat .azure/docs/README_base.md > README.md
echo ' ' >> README.md

echo "## Packages" >> README.md
echo " " >> README.md
echo " " >> README.md
echo "Links to the extended documentation of packaged modules, available through gh-pages:" >> README.md
echo " " >> README.md

.azure/tools/update_aasf_links.sh >> README.md