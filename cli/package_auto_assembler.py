import logging
import shutil
import os
import click
import yaml
from package_auto_assembler.package_auto_assembler import PackageAutoAssembler, ReleaseNotesHandler, VersionHandler


__cli_metadata__ = {
    "name" : "paa"
}


@click.group()
@click.pass_context
def cli(ctx):
    """Package Auto Assembler CLI tool."""
    ctx.ensure_object(dict)

test_install_config = {
        "module_dir" : "python_modules",
        "cli_dir" : "cli",
        "mapping_filepath" : "package_mapping.json",
        "include_local_dependecies" : True,
        "dependencies_dir" : None,
        "release_notes_dir" : "./release_notes/",
        "example_notebooks_path" : "./example_notebooks/",
        "versions_filepath" : "lsts_package_versions.yml",
        "log_filepath" : "version_logs.csv",
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
        "version_increment_type" : "patch",
        "use_commit_messages" : True
    }

@click.command()
@click.pass_context
def init_config(ctx):
    """Initialize config file"""

    config = ".paa.config"

    if not os.path.exists(config):
        with open(config, 'w', encoding='utf-8') as file:
            yaml.dump(test_install_config, file, sort_keys=False)

        click.echo(f"Config file {config} initialized!")
        click.echo(f"Edit it to your preferance.")
    else:
        click.echo(f"Config file already exists in {config}!")



@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--default-version', 'default_version', type=str, required=False, help='Default version.')
@click.option('--check-vulnerabilities', 'check_vulnerabilities', is_flag=True, type=bool, required=False, help='If checked, checks module dependencies with pip-audit for vulnerabilities.')
@click.option('--keep-temp-files', 'keep_temp_files', is_flag=True, type=bool, required=False, help='If checked, setup directory won\'t be removed after setup is done.')
@click.option('--skip-deps-install', 'skip_deps_install', is_flag=True, type=bool, required=False, help='If checked, existing dependencies from env will be reused.')
@click.pass_context
def test_install(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        dependencies_dir,
        default_version,
        check_vulnerabilities,
        skip_deps_install,
        keep_temp_files):
    """Test install module into local environment."""

    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    test_install_config["loggerLvl"] = logging.INFO

    paa_params = {
        "module_name" : f"{module_name}",
        "module_filepath" : os.path.join(test_install_config['module_dir'], f"{module_name}.py"),
        "cli_module_filepath" : os.path.join(test_install_config['cli_dir'], f"{module_name}.py"),
        "mapping_filepath" : test_install_config["mapping_filepath"],
        "dependencies_dir" : test_install_config["dependencies_dir"],
        "setup_directory" : f"./{module_name}",
        "classifiers" : test_install_config["classifiers"],
        "default_version" : test_install_config["default_version"]
    }

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath

    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir

    if default_version:
        paa_params["default_version"] = default_version
    if check_vulnerabilities:
        paa_params["check_vulnerabilities"] = True
    else:
        paa_params["check_vulnerabilities"] = False

    if skip_deps_install:
        paa_params["skip_deps_install"] = True

    if keep_temp_files:
        remove_temp_files = False
    else:
        remove_temp_files = True

    paa = PackageAutoAssembler(
        **paa_params
    )

    if paa.metadata_h.is_metadata_available():

        paa.add_metadata_from_module()
        paa.add_metadata_from_cli_module()
        paa.metadata['version'] = paa.default_version

        paa.prep_setup_dir()

        if test_install_config["include_local_dependecies"]:
            paa.merge_local_dependacies()

        paa.add_requirements_from_module()
        paa.add_requirements_from_cli_module()

        paa.prep_setup_file()
        paa.make_package()
        click.echo(f"Module {module_name.replace('_','-')} prepared as a package.")
        paa.test_install_package(remove_temp_files = remove_temp_files)
        click.echo(f"Module {module_name.replace('_','-')} installed in local environment, overwriting previous version!")

    else:
        paa.logger.info(f"Metadata condition was not fullfield for {module_name.replace('_','-')}")


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--kernel-name', 'kernel_name', type=str, required=False, help='Kernel name.')
@click.option('--python-version', 'python_version', type=str, required=False, help='Python version.')
@click.option('--default-version', 'default_version', type=str, required=False, help='Default version.')
@click.option('--ignore-vulnerabilities-check', 'ignore_vulnerabilities_check', is_flag=True, type=bool, required=False, help='If checked, does not check module dependencies with pip-audit for vulnerabilities.')
@click.option('--example-notebook-path', 'example_notebook_path', type=str, required=False, help='Path to .ipynb file to be used as README.')
@click.option('--execute-notebook', 'execute_notebook', is_flag=True, type=bool, required=False, help='If checked, executes notebook before turning into README.')
@click.option('--log-filepath', 'log_filepath', type=str, required=False, help='Path to logfile to record version change.')
@click.option('--versions-filepath', 'versions_filepath', type=str, required=False, help='Path to file where latest versions of the packages are recorded.')
@click.pass_context
def make_package(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        dependencies_dir,
        kernel_name,
        python_version,
        default_version,
        ignore_vulnerabilities_check,
        example_notebook_path,
        execute_notebook,
        log_filepath,
        versions_filepath):
    """Package with package-auto-assembler."""

    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    test_install_config["loggerLvl"] = logging.INFO

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
        "versions_filepath" : test_install_config["versions_filepath"],
        "log_filepath" : test_install_config["log_filepath"],
        "use_commit_messages" : test_install_config["use_commit_messages"]
    }

    if test_install_config["release_notes_dir"]:
        paa_params["release_notes_filepath"] = os.path.join(test_install_config["release_notes_dir"],
                                                            f"{module_name}.md")

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

    if ignore_vulnerabilities_check:
        paa_params["check_vulnerabilities"] = False
    else:
        paa_params["check_vulnerabilities"] = True

    if example_notebook_path:
        paa_params["example_notebook_path"] = example_notebook_path
    else:
        paa_params["example_notebook_path"] = os.path.join(test_install_config["example_notebooks_path"],
                                                           f"{module_name}.ipynb")
    if log_filepath:
        paa_params["log_filepath"] = log_filepath
    if versions_filepath:
        paa_params["versions_filepath"] = versions_filepath

    paa = PackageAutoAssembler(
        **paa_params
    )

    if paa.metadata_h.is_metadata_available():

        paa.add_metadata_from_module()
        paa.add_metadata_from_cli_module()
        paa.add_or_update_version()
        if test_install_config["use_commit_messages"]:
            paa.add_or_update_release_notes()
        paa.prep_setup_dir()

        if test_install_config["include_local_dependecies"]:
            paa.merge_local_dependacies()

        paa.add_requirements_from_module()
        paa.add_requirements_from_cli_module()
        paa.add_readme(execute_notebook = execute_notebook)
        paa.prep_setup_file()
        paa.make_package()
        click.echo(f"Module {module_name.replace('_','-')} prepared as a package.")

    else:
        paa.logger.info(f"Metadata condition was not fullfield for {module_name.replace('_','-')}")

@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.pass_context
def check_vulnerabilities(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        dependencies_dir):
    """Check vulnerabilities of the module."""

    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    test_install_config["loggerLvl"] = logging.INFO

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
        "versions_filepath" : test_install_config["versions_filepath"],
        "log_filepath" : test_install_config["log_filepath"],
        "check_vulnerabilities" : True
    }

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath
    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir

    paa = PackageAutoAssembler(
        **paa_params
    )

    if paa.metadata_h.is_metadata_available():


        paa.add_metadata_from_module()
        paa.add_metadata_from_cli_module()
        paa.metadata['version'] = paa.default_version
        paa.prep_setup_dir()

        try:
            if test_install_config["include_local_dependecies"]:
                paa.merge_local_dependacies()

            paa.add_requirements_from_module()
            paa.add_requirements_from_cli_module()
        except Exception as e:
            print("")
        finally:
            shutil.rmtree(paa.setup_directory)

    else:
        paa.logger.info(f"Metadata condition was not fullfield for {module_name.replace('_','-')}")

@click.command()
@click.argument('label_name')
@click.option('--version', type=str, required=False, help='Version of new release.')
@click.option('--notes', type=str, required=False, help='Optional manually provided notes string, where each note is separated by ; and increment type is provide in accordance to paa documentation.')
@click.option('--notes-filepath', 'notes_filepath', type=str, required=False, help='Path to .md wit release notes.')
@click.option('--max-search-depth', 'max_search_depth', type=str, required=False, help='Max search depth in commit history.')
@click.option('--use-pip-latest', 'usepip', is_flag=True, type=bool, required=False, help='If checked, attempts to pull latest version from pip.')
@click.pass_context
def update_release_notes(ctx,
        label_name,
        version,
        notes,
        notes_filepath,
        max_search_depth,
        usepip):
    """Update release notes."""

    label_name = label_name.replace('-','_')

    if notes_filepath is None:
        release_notes_path = "./release_notes"
        notes_filepath = os.path.join(release_notes_path,
                                            f"{label_name}.md")

    if usepip:
        usepip = True
    else:
        usepip = False
    
    rnh_params = {
        'filepath' : notes_filepath,
        'label_name' : label_name,
        'version' : "0.0.1"
    }

    vh_params = {
        'versions_filepath' : '',
        'log_filepath' : '',
        'read_files' : False,
        'default_version' : "0.0.0"
    }

    if max_search_depth:
        rnh_params['max_search_depth'] = max_search_depth

    rnh = ReleaseNotesHandler(
        **rnh_params
    )

    if notes:
        if not notes.startswith('['):
            notes = ' ' + notes

        rnh.commit_messages = [f'[{label_name}]{notes}']
        rnh._filter_commit_messages_by_package()
        rnh._clean_and_split_commit_messages()

    if version is None:

        rnh.extract_version_update()

        version_increment_type = rnh.version_update_label

        version = rnh.extract_latest_version()

        if rnh.version != '0.0.1':
            version = rnh.version
        else:

            vh = VersionHandler(
                **vh_params)

            if version:
                vh.versions[label_name] = version

            vh.increment_version(package_name = label_name,
                                                version = None,
                                                increment_type = version_increment_type,
                                                default_version = version,
                                                save = False,
                                                usepip = usepip)

            version = vh.get_version(package_name=label_name)

    rnh.version = version

    rnh.create_release_note_entry()

    rnh.save_release_notes()
    click.echo(f"Release notes for {label_name} with version {version} were updated!")

    

cli.add_command(init_config, "init-config")
cli.add_command(test_install, "test-install")
cli.add_command(make_package, "make-package")
cli.add_command(check_vulnerabilities, "check-vulnerabilities")
cli.add_command(update_release_notes, "update-release-notes")


if __name__ == "__main__":
    cli()

