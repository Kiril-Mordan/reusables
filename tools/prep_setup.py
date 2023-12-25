from setuptools import setup
import importlib.util
import os
import sys

def get_package_metadata(module_name, modules_path):
    module_path = os.path.join(modules_path, module_name + '.py')
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__package_metadata__

def read_requirements_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip() and not line.startswith('#')]


def write_setup_file(module_name, metadata, install_requires, classifiers):
    metadata_str = ', '.join([f'{key}="{value}"' for key, value in metadata.items()])
    setup_content = f"""from setuptools import setup

setup(
    name="{module_name}",
    packages=["{module_name}"],
    install_requires={install_requires},
    classifiers={classifiers},
    {metadata_str}
)
"""
    with open('setup_dir/setup.py', 'w') as file:
        file.write(setup_content)

if __name__ == "__main__":

    modules_path = './python_modules'
    requirements_path = './env_spec'

    classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "License :: OSI Approved :: MIT License",
            "Topic :: Scientific/Engineering",
        ]

    module_to_build = sys.argv[1] #"mock_vector_database"

    requirements_file = os.path.join(requirements_path, f"requirements_{module_to_build}.txt")

    install_requires = read_requirements_file(requirements_file)
    metadata = get_package_metadata(module_name = module_to_build,
                                    modules_path = modules_path)


    write_setup_file(module_name = module_to_build,
                  metadata = metadata,
                  install_requires = install_requires,
                  classifiers = classifiers)
