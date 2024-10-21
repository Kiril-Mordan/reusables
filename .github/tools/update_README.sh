#!/bin/bash
chmod +x .github/tools/update_gh_pages_links.sh
.github/tools/update_gh_pages_links.sh
cat docs/README_base.md > README.md
echo ' ' >> README.md
cat links.md >> README.md
