import os
import click
import yaml

from package_auto_assembler.package_auto_assembler import PackageAutoAssembler

@click.group()
@click.pass_context
def cli(ctx):
    """Package Auto Assembler CLI tool."""
    ctx.ensure_object(dict)

@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli_module_filepath', type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--kernel_name', type=str, required=False, help='Kernel name.')
@click.option('--python_version', type=str, required=False, help='Python version.')
@click.option('--default_version', type=str, required=False, help='Default version.')
@click.option('--check_vulnerabilities', type=bool, required=False, help='If True, checks module dependencies with pip-audit for vulnerabilities.')
@click.option('--remove_temp_files', type=bool, required=False, help='If False, setup directory won\'t be removed after setup is done.')
@click.pass_context
def package(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        dependencies_dir,
        kernel_name,
        python_version,
        default_version,
        check_vulnerabilities,
        remove_temp_files):
    """Test install module for .py file in local environment"""

    test_install_config = {
        "module_dir" : "python_modules",
        "cli_dir" : "cli",
        "mapping_filepath" : "./env_spec/package_mapping.json",
        "dependencies_dir" : None,
        "classifiers" : ['Development Status :: 3 - Alpha',
                        'Intended Audience :: Developers',
                        'Intended Audience :: Science/Research',
                        'Programming Language :: Python :: 3',
                        'Programming Language :: Python :: 3.9',
                        'Programming Language :: Python :: 3.10',
                        'Programming Language :: Python :: 3.11',
                        'License :: OSI Approved :: MIT License',
                        'Topic :: Scientific/Engineering'],
        "kernel_name" : 'python3',
        "python_version" : "3.10",
        "default_version" : "0.0.0",
        "check_vulnerabilities" : False,
        "remove_temp_files" : True
    }

    if config is None:
        config = "paa_config.yml"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    paa_params = {
        "module_name" : f"{module_name}",
        "module_filepath" : os.path.join(test_install_config['module_dir'], f"{module_name}.py"),
        "cli_module_filepath" : os.path.join(test_install_config['cli_dir'], f"{module_name}.py"),
        "mapping_filepath" : test_install_config["mapping_filepath"],
        "dependencies_dir" : test_install_config["dependencies_dir"],
        "setup_directory" : f"./{module_name}",
        "classifiers" : test_install_config["classifiers"],
        "kernel_name" : test_install_config["kernel_name"],
        "python_version" : test_install_config["python_version"],
        "default_version" : test_install_config["default_version"],
        "check_vulnerabilities" : test_install_config["check_vulnerabilities"]
    }

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath
    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir
    if kernel_name:
        paa_params["kernel_name"] = kernel_name
    if python_version:
        paa_params["python_version"] = python_version
    if default_version:
        paa_params["default_version"] = default_version
    if check_vulnerabilities:
        paa_params["check_vulnerabilities"] = check_vulnerabilities
    if remove_temp_files is None:
        remove_temp_files = test_install_config["remove_temp_files"]

    paa = PackageAutoAssembler(
        **paa_params
    )

    paa.add_metadata_from_module()
    #paa.add_or_update_version()
    paa.metadata['version'] = paa.default_version
    paa.prep_setup_dir()
    paa.add_requirements_from_module()
    #paa.add_readme()
    paa.prep_setup_file()
    paa.make_package()
    paa.test_install_package(remove_temp_files = remove_temp_files)


    click.echo(f"Module {module_name} installed in local environment, overwriting previous version!")


cli.add_command(package)

if __name__ == "__main__":
    cli()

