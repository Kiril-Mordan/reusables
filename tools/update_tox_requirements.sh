#!/bin/bash

module_name="${@}"

cp "./env_spec/requirements_dev.txt" "./env_spec/requirements_tox.txt"
echo "" >> "./env_spec/requirements_tox.txt"
cat "./env_spec/requirements_$module_name.txt" >> "./env_spec/requirements_tox.txt"