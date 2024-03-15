import re
import os
import json
import argparse
from package_auto_assembler import RequirementsHandler

def load_package_mappings(mapping_file):
    """
    Get file with mappings for packages which immport names differ from install names.
    """

    with open(mapping_file, 'r') as file:
        return json.load(file)

if __name__ == "__main__":


    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract requirements from module.')
    parser.add_argument('module_name', type=str, help='Name of the module')
    args = parser.parse_args()

    # Use the argument
    module_name = args.module_name

    mapping_file = 'env_spec/package_mapping.json'
    path_to_module = "python_modules"
    output_path = "env_spec/"
    output_file_prefix = "requirements_"
    custom_modules_path = 'python_modules'
    python_version = '3.9'

    package_mappings = load_package_mappings(mapping_file)

    # define RequirementsHandler
    rh = RequirementsHandler(
        # optional/required later
        module_filepath = os.path.join(path_to_module, module_name),
        package_mappings = package_mappings,
        requirements_output_path = output_path,
        output_requirements_prefix = output_file_prefix,
        python_version = python_version
    )
    rh.extract_requirements()
    rh.write_requirements_file()

    print("requirements.txt generated successfully.")
