#!/bin/bash

module_name="${@}"
module_reqs_file=".paa/requirements/requirements_${module_name}.txt"

cp ".paa/requirements_dev.txt" ".paa/requirements/requirements_tox.txt"
echo "" >> ".paa/requirements/requirements_tox.txt"
if [ ! -f "$module_reqs_file" ]; then
  echo "Module requirements file not found: $module_reqs_file"
  echo "Ensure changed module detection resolved to a top-level package module."
  exit 1
fi
cat "$module_reqs_file" >> ".paa/requirements/requirements_tox.txt"
