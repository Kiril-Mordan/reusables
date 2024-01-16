from python_modules.package_auto_assembler import PackageAutoAssembler
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description='Make package for module.')
parser.add_argument('module_name', type=str, help='Name of the module')
args = parser.parse_args()

module_name = args.module_name

paa = PackageAutoAssembler(
    # required
    module_name = "shouterlog",
    module_filepath  = f"./python_modules/{module_name}.py",
    # optional
    mapping_filepath = "./env_spec/package_mapping.json",
    dependencies_dir = None,
    example_notebook_path = f"./example_notebooks/{module_name}.ipynb",
    versions_filepath = './env_spec/lsts_package_versions.yml',
    log_filepath = './env_spec/version_logs.csv',
    setup_directory = "./{module_name}",
    classifiers = ['Development Status :: 3 - Alpha',
                    'Intended Audience :: Developers',
                    'Intended Audience :: Science/Research',
                    'Programming Language :: Python :: 3',
                    'Programming Language :: Python :: 3.9',
                    'Programming Language :: Python :: 3.10',
                    'Programming Language :: Python :: 3.11',
                    'License :: OSI Approved :: MIT License',
                    'Topic :: Scientific/Engineering'],
    kernel_name = 'python3',
    python_version = "3.10",
    version_increment_type = "patch",
    default_version = "0.0.1"
)

if paa.metadata_h.is_metadata_available():

    paa.add_metadata_from_module()
    paa.add_or_update_version()
    paa.prep_setup_dir()
    paa.add_requirements_from_module()
    paa.add_readme()
    paa.prep_setup_file()
    paa.make_package()
else:
    paa.logger.info(f"Metadata condition was not fullfield for {module_name}")