import re
import os
from stdlib_list import stdlib_list


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

def extract_requirements(path_to_module, module_name, custom_modules, python_version='3.8'):

    file_path = f"{path_to_module}/{module_name}.py"

    # Regex pattern for import statements (both 'import' and 'from ... import ...') and version comments
    pattern = re.compile(r"(?:import (\S+)|from (\S+) import).*?#(?:\s*(==|>=|<=|>|<)\s*([0-9.]+))?")

    # init requirements
    requirements = [f'### {module_name}']

    with open(file_path, 'r') as file:
        for line in file:
            match = pattern.match(line)
            if match:
                module_import, module_from, version_constraint, version = match.groups()
                module = module_from if module_from else module_import

                # Skip standard library and custom modules
                if is_standard_library(module) or module in custom_modules:
                    continue

                if version is not None:
                    requirements.append(f"{module}{version_constraint}{version}")
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
    module_name = "mock_vector_database"
    path_to_module = "python_modules"
    output_path = "env_spec"
    output_file_prefix = "requirements_"
    custom_modules_path = 'python_modules'
    python_version = '3.9'

    custom_modules = list_custom_modules(custom_modules_path)
    requirements = extract_requirements(path_to_module = path_to_module,
                                        module_name = module_name,
                                        python_version=python_version,
                                        custom_modules = custom_modules)

    write_requirements_file(requirements = requirements,
                            module_name = module_name,
                            output_path = output_path,
                            prefix = output_file_prefix)
    print("requirements.txt generated successfully.")
