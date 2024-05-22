import os
import sys
from package_auto_assembler import PackageAutoAssembler



if __name__ == "__main__":

    module_name = sys.argv[1]

    paa = PackageAutoAssembler(
        # required
        module_name = f"{module_name}",
        module_filepath  = f"./python_modules/{module_name}.py",
        # optional
        mapping_filepath = "./env_spec/package_mapping.json",
        dependencies_dir = None,
        #example_notebook_path = f"./example_notebooks/{module_name}.ipynb",
        #versions_filepath = './env_spec/lsts_package_versions.yml',
        #log_filepath = './env_spec/version_logs.csv',
        setup_directory = f"./{module_name}",
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
        #version_increment_type = "patch",
        default_version = "0.0.0"
    )

    paa.add_metadata_from_module()
    #paa.add_or_update_version()
    paa.metadata['version'] = paa.default_version
    paa.prep_setup_dir()
    paa.add_requirements_from_module()
    #paa.add_readme()
    paa.prep_setup_file()
    paa.make_package()
    paa.test_install_package()

