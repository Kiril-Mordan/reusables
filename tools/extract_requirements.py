import re
import os
import json
import argparse
from stdlib_list import stdlib_list

def load_package_mappings(mapping_file):
    """
    Get file with mappings for packages which immport names differ from install names.
    """

    with open(mapping_file, 'r') as file:
        return json.load(file)


def list_custom_modules(custom_modules_path):
    """
    List all custom module names in the specified directory.
    """
    custom_modules = set()
    for filename in os.listdir(custom_modules_path):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename.rsplit('.', 1)[0]
            custom_modules.add(module_name)
    return custom_modules

def is_standard_library(module_name, python_version='3.8'):
    """
    Check if a module is part of the standard library for the given Python version.
    """
    return module_name in stdlib_list(python_version)

def extract_requirements(path_to_module, module_name, custom_modules,package_mappings = {}, python_version='3.8'):

    file_path = f"{path_to_module}/{module_name}.py"

    # Separate regex patterns for 'import' and 'from ... import ...' statements
    import_pattern = re.compile(r"import (\S+)(?:\s+#(?:\s*(==|>=|<=|>|<)\s*([0-9.]+)))?")
    from_import_pattern = re.compile(r"from (\S+) import.*(?:\s+#(?:\s*(==|>=|<=|>|<)\s*([0-9.]+)))?")

    requirements = [f'### {module_name}']

    with open(file_path, 'r') as file:
        for line in file:
            import_match = import_pattern.match(line)
            from_import_match = from_import_pattern.match(line)

            if import_match:
                module, version_constraint, version = import_match.groups()
            elif from_import_match:
                module, version_constraint, version = from_import_match.groups()
            else:
                continue

            # Extract the base package name
            module = module.split('.')[0]

            # Skip standard library and custom modules
            if is_standard_library(module, python_version) or module in custom_modules or module == path_to_module:
                continue

            # Use the mapping to get the correct package name
            module = package_mappings.get(module, module)

            version_info = f"{version_constraint}{version}" if version_constraint and version else ""

            # Print for debugging
            # print(f"Matched line: {line.strip()}, Module: {module}, Version: {version_info}")

            if version_info:
                requirements.append(f"{module}{version_info}")
            else:
                requirements.append(module)

    return requirements

def write_requirements_file(requirements,
                            module_name,
                            output_path,
                            prefix = "requirements_"):

    output_file = f"{output_path}/{prefix}{module_name}.txt"

    with open(output_file, 'w') as file:
        for req in requirements:
            file.write(req + '\n')


if __name__ == "__main__":

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract requirements from module.')
    parser.add_argument('module_name', type=str, help='Name of the module')
    args = parser.parse_args()

    # Use the argument
    module_name = args.module_name

    mapping_file = 'env_spec/package_mapping.json'
    path_to_module = "python_modules"
    output_path = "env_spec"
    output_file_prefix = "requirements_"
    custom_modules_path = 'python_modules'
    python_version = '3.9'

    package_mappings = load_package_mappings(mapping_file)
    custom_modules = list_custom_modules(custom_modules_path)
    requirements = extract_requirements(path_to_module = path_to_module,
                                        module_name = module_name,
                                        python_version = python_version,
                                        package_mappings = package_mappings,
                                        custom_modules = custom_modules)

    write_requirements_file(requirements = requirements,
                            module_name = module_name,
                            output_path = output_path,
                            prefix = output_file_prefix)
    print("requirements.txt generated successfully.")
