import logging
import shutil
import os
import click #==8.1.7
import yaml
import importlib
import importlib.metadata
import importlib.resources as pkg_resources
import ast

from package_auto_assembler.package_auto_assembler import (
    PackageAutoAssembler, 
    ReleaseNotesHandler, 
    VersionHandler,
    RequirementsHandler,
    DependenciesAnalyser,
    FastApiHandler,
    ArtifactsHandler,
    PprHandler,
    StreamlitHandler)


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
    "example_notebooks_path" : "example_notebooks",
    "versions_filepath" : "lsts_package_versions.yml",
    "log_filepath" : "version_logs.csv",
    "include_local_dependecies" : True,
    "use_commit_messages" : True,
    "check_vulnerabilities" : True,
    "check_dependencies_licenses" : False,
    "add_artifacts" : True,
    "add_mkdocs_site" : False,
    "artifacts_dir" : None,
    "drawio_dir" : None,
    "tests_dir" : None,
    "cli_dir" : None,
    "cli_docs_dir" : None,
    "api_routes_dir" : None,
    "streamlit_dir" : None,
    "docs_dir" : None,
    "release_notes_dir" : None,
    "mapping_filepath" : None,
    "licenses_filepath" : None,
    "dependencies_dir" : None,
    "license_path" : None,
    "license_label" : None,
    "license_badge" : None,
    "docs_url" : None,
    "classifiers" : None,
    "allowed_licenses" : None,
    "kernel_name" : None,
    "python_version" : None,
    "default_version" : None,
    "version_increment_type" : None
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
@click.pass_context
def init_paa(ctx):
    """Initialize paa tracking files"""

    st = PprHandler().init_paa_dir()

    if st:
        click.echo(f"PAA tracking files initialized!")



@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--fastapi-routes-filepath', 'fastapi_routes_filepath',  type=str, required=False, help='Path to .py file that routes for fastapi.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--default-version', 'default_version', type=str, required=False, help='Default version.')
@click.option('--check-vulnerabilities', 'check_vulnerabilities', is_flag=True, type=bool, required=False, help='If checked, checks module dependencies with pip-audit for vulnerabilities.')
@click.option('--build-mkdocs', 'build_mkdocs', is_flag=True, type=bool, required=False, help='If checked, builds mkdocs documentation.')
@click.option('--check-licenses', 'check_licenses', is_flag=True, type=bool, required=False, help='If checked, checks module dependencies licenses.')
@click.option('--keep-temp-files', 'keep_temp_files', is_flag=True, type=bool, required=False, help='If checked, setup directory won\'t be removed after setup is done.')
@click.option('--skip-deps-install', 'skip_deps_install', is_flag=True, type=bool, required=False, help='If checked, existing dependencies from env will be reused.')
@click.pass_context
def test_install(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        fastapi_routes_filepath,
        dependencies_dir,
        default_version,
        check_vulnerabilities,
        build_mkdocs,
        check_licenses,
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
        "config_filepath" : config,
        "module_name" : f"{module_name}",
        "module_filepath" : os.path.join(test_install_config['module_dir'], f"{module_name}.py"),
        "mapping_filepath" : test_install_config.get("mapping_filepath"),
        "licenses_filepath" : test_install_config.get("licenses_filepath"),
        "dependencies_dir" : test_install_config.get("dependencies_dir"),
        "setup_directory" : f"./{module_name}",
        "add_artifacts" : test_install_config.get("add_artifacts"),
        "artifacts_filepaths" : test_install_config.get("artifacts_filepaths"),
        "docs_path" : test_install_config.get("docs_dir"),
        "license_badge" : test_install_config.get("license_badge"),
        "add_mkdocs_site" : False,
        "check_dependencies_licenses" : False,
        "check_vulnerabilities" : False

    }

    if test_install_config.get("tests_dir"):
        paa_params["tests_dir"] = os.path.join(
            test_install_config['tests_dir'], f"{module_name}")

    if test_install_config.get("drawio_dir"):
        paa_params["drawio_filepath"] = os.path.join(
            test_install_config['drawio_dir'], f"{module_name}.drawio")

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("allowed_licenses"):
        paa_params["allowed_licenses"] = test_install_config["allowed_licenses"]

    if test_install_config.get("cli_dir"):
        paa_params["cli_module_filepath"] = os.path.join(
            test_install_config['cli_dir'], f"{module_name}.py")

    if test_install_config.get("api_routes_dir"):
        paa_params["fastapi_routes_filepath"] = os.path.join(
            test_install_config['api_routes_dir'], f"{module_name}.py")

    if test_install_config.get("streamlit_dir"):
        paa_params["streamlit_filepath"] = os.path.join(
            test_install_config['streamlit_dir'], f"{module_name}.py")

    if test_install_config.get("artifacts_dir"):
        paa_params["artifacts_dir"] = os.path.join(
            test_install_config["artifacts_dir"], module_name)

    if test_install_config.get("release_notes_dir"):
        paa_params["release_notes_filepath"] = os.path.join(test_install_config["release_notes_dir"],
                                                            f"{module_name}.md")
    if test_install_config.get("cli_docs_dir"):
        paa_params["cli_docs_filepath"] = os.path.join(test_install_config["cli_docs_dir"],
                                                            f"{module_name}.md")

    if build_mkdocs:
        paa_params["add_mkdocs_site"] = True

    if test_install_config.get("docs_file_paths"):
        paa_params["docs_file_paths"] = test_install_config.get("docs_file_paths")

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if fastapi_routes_filepath:
        paa_params["fastapi_routes_filepath"] = fastapi_routes_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath

    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir

    if default_version:
        paa_params["default_version"] = default_version
    if check_vulnerabilities:
        paa_params["check_vulnerabilities"] = True
    
    if check_licenses:
        paa_params["check_dependencies_licenses"] = True

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
        paa.add_requirements_from_api_route()
        paa.add_requirements_from_streamlit()
        paa.make_mkdocs_site()
        paa.prepare_artifacts()
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
@click.option('--fastapi-routes-filepath', 'fastapi_routes_filepath',  type=str, required=False, help='Path to .py file that routes for fastapi.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--kernel-name', 'kernel_name', type=str, required=False, help='Kernel name.')
@click.option('--python-version', 'python_version', type=str, required=False, help='Python version.')
@click.option('--default-version', 'default_version', type=str, required=False, help='Default version.')
@click.option('--ignore-vulnerabilities-check', 'ignore_vulnerabilities_check', is_flag=True, type=bool, required=False, help='If checked, does not check module dependencies with pip-audit for vulnerabilities.')
@click.option('--ignore-licenses-check', 'ignore_licenses_check', is_flag=True, type=bool, required=False, help='If checked, does not check module licenses for unexpected ones.')
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
        fastapi_routes_filepath,
        dependencies_dir,
        kernel_name,
        python_version,
        default_version,
        ignore_vulnerabilities_check,
        ignore_licenses_check,
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
        "config_filepath" : config,
        "module_name" : f"{module_name}",
        "module_filepath" : os.path.join(test_install_config['module_dir'], f"{module_name}.py"),
        "mapping_filepath" : test_install_config.get("mapping_filepath"),
        "licenses_filepath" : test_install_config.get("licenses_filepath"),
        "dependencies_dir" : test_install_config.get("dependencies_dir"),
        "setup_directory" : f"./{module_name}",
        "versions_filepath" : test_install_config["versions_filepath"],
        "log_filepath" : test_install_config["log_filepath"],
        "use_commit_messages" : test_install_config["use_commit_messages"],
        "license_path" : test_install_config.get("license_path", None),
        "license_label" : test_install_config.get("license_label", None),
        "license_badge" : test_install_config.get("license_badge"),
        "docs_url" : test_install_config.get("docs_url", None),
        "add_artifacts" : test_install_config.get("add_artifacts"),
        "add_mkdocs_site" : test_install_config.get("add_mkdocs_site"),
        "artifacts_filepaths" : test_install_config.get("artifacts_filepaths"),
        "docs_path" : test_install_config.get("docs_dir"),
        "check_vulnerabilities" : test_install_config.get("check_vulnerabilities", True),
        "check_dependencies_licenses" : test_install_config.get("check_dependencies_licenses", True)
    }

    if test_install_config.get("tests_dir"):
        paa_params["tests_dir"] = os.path.join(
            test_install_config['tests_dir'], f"{module_name}")

    if test_install_config.get("drawio_dir"):
        paa_params["drawio_filepath"] = os.path.join(
            test_install_config['drawio_dir'], f"{module_name}.drawio")

    if test_install_config.get("example_notebooks_path"):
        paa_params["example_notebook_path"] = os.path.join(test_install_config["example_notebooks_path"],
                                                           f"{module_name}.ipynb")

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("python_version"):
        paa_params["python_version"] = test_install_config["python_version"]

    if test_install_config.get("kernel_name"):
        paa_params["kernel_name"] = test_install_config["kernel_name"]

    if test_install_config.get("allowed_licenses"):
        paa_params["allowed_licenses"] = test_install_config["allowed_licenses"]

    if test_install_config.get("cli_dir"):
        paa_params["cli_module_filepath"] = os.path.join(
            test_install_config['cli_dir'], f"{module_name}.py")

    if test_install_config.get("api_routes_dir"):
        paa_params["fastapi_routes_filepath"] = os.path.join(
            test_install_config['api_routes_dir'], f"{module_name}.py")

    if test_install_config.get("streamlit_dir"):
        paa_params["streamlit_filepath"] = os.path.join(
            test_install_config['streamlit_dir'], f"{module_name}.py")

    if test_install_config.get("artifacts_dir"):
        paa_params["artifacts_dir"] = os.path.join(
            test_install_config["artifacts_dir"], module_name)

    if test_install_config.get("release_notes_dir"):
        paa_params["release_notes_filepath"] = os.path.join(test_install_config["release_notes_dir"],
                                                            f"{module_name}.md")
    if test_install_config.get("cli_docs_dir"):
        paa_params["cli_docs_filepath"] = os.path.join(test_install_config["cli_docs_dir"],
                                                            f"{module_name}.md")

    if test_install_config.get("docs_file_paths"):
        paa_params["docs_file_paths"] = test_install_config.get("docs_file_paths")

    if test_install_config.get("license_badge"):
        paa_params["license_badge"] = test_install_config.get("license_badge")

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if fastapi_routes_filepath:
        paa_params["fastapi_routes_filepath"] = fastapi_routes_filepath
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

    if ignore_licenses_check:
        paa_params["check_dependencies_licenses"] = False

    if example_notebook_path:
        paa_params["example_notebook_path"] = example_notebook_path
    
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
        paa.add_requirements_from_api_route()
        paa.add_requirements_from_streamlit()
        paa.add_readme(execute_notebook = execute_notebook)
        paa.make_mkdocs_site()
        paa.prepare_artifacts()
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
        "versions_filepath" : test_install_config["versions_filepath"],
        "log_filepath" : test_install_config["log_filepath"],
        "check_vulnerabilities" : True,
        "add_artifacts" : False
    }

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("python_version"):
        paa_params["python_version"] = test_install_config["python_version"]

    if test_install_config.get("kernel_name"):
        paa_params["kernel_name"] = test_install_config["kernel_name"]

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
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--license-mapping-filepath', 'licenses_filepath', type=str, required=False, help='Path to .json file that maps license labels to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--skip-normalize-labels', 
              'skip_normalize_labels', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, package license labels are not normalized.')
@click.pass_context
def check_licenses(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        licenses_filepath,
        cli_module_filepath,
        dependencies_dir,
        skip_normalize_labels):
    """Check licenses of the module."""

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
        "licenses_filepath" : test_install_config["licenses_filepath"],
        "dependencies_dir" : test_install_config["dependencies_dir"],
        "setup_directory" : f"./{module_name}",
        "versions_filepath" : test_install_config["versions_filepath"],
        "log_filepath" : test_install_config["log_filepath"],
        "check_vulnerabilities" : False,
        "check_dependencies_licenses" : True,
        "add_artifacts" : False
    }

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("python_version"):
        paa_params["python_version"] = test_install_config["python_version"]

    if test_install_config.get("kernel_name"):
        paa_params["kernel_name"] = test_install_config["kernel_name"]

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath
    if licenses_filepath:
        paa_params["licenses_filepath"] = licenses_filepath
    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir

    paa = PackageAutoAssembler(
        **paa_params
    )

    if skip_normalize_labels:
        normalize_labels = False
    else:
        normalize_labels = True

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

@click.command()
@click.option('--tags', 
              multiple=True, 
              required=False, 
              help='Keyword tag filters for the package.')
@click.pass_context
def show_module_list(ctx,
        tags):
    """Shows module list."""

    tags = list(tags)

    if tags == []:
        tags = ['aa-paa-tool']
    # else:
    #     tags.append('aa-paa-tool')

    da = DependenciesAnalyser()

    packages = da.filter_packages_by_tags(tags)
    if packages:
        # Calculate the maximum length of package names for formatting
        max_name_length = max(len(pkg[0]) for pkg in packages) if packages else 0
        max_version_length = max(len(pkg[1]) for pkg in packages) if packages else 0
        
        # Print the header
        header_name = "Package"
        header_version = "Version"
        click.echo(f"{header_name:<{max_name_length}} {header_version:<{max_version_length}}")
        click.echo(f"{'-' * max_name_length} {'-' * max_version_length}")

        # Print each package and its version
        for package, version in packages:
            click.echo(f"{package:<{max_name_length}} {version:<{max_version_length}}")
    else:
        click.echo(f"No packages found matching all tags {tags}")

@click.command()
@click.argument('label_name')
@click.pass_context
def show_module_artifacts(ctx,
        label_name):
    """Shows module artifacts."""

    ah = ArtifactsHandler(
        module_name = label_name.replace('-','_')
    )

    package_artifacts = ah.get_packaged_artifacts()

    if package_artifacts:
        # Print each package and its version
        for artifact, path in package_artifacts.items():
            click.echo(f"{artifact}")
    else:
        click.echo(f"No package artifacts found for {label_name}")

@click.command()
@click.argument('label_name')
# @click.option('--is-cli', 
#               'get_paa_cli_status', 
#               is_flag=True, 
#               type=bool, 
#               required=False, 
#               help='If checked, returns true when cli interface is available.')
@click.option('--keywords', 
              'get_keywords', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns keywords for the package.')
@click.option('--classifiers', 
              'get_classifiers', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns classfiers for the package.')
@click.option('--docstring', 
              'get_docstring', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns docstring of the package.')
@click.option('--author', 
              'get_author', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns author of the package.')
@click.option('--author-email', 
              'get_author_email', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns author email of the package.')
@click.option('--version', 
              'get_version', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns installed version of the package.')
@click.option('--license_label', 
              'get_license_label', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns license label of the package.')
# @click.option('--license', 
#               'get_license', 
#               is_flag=True, 
#               type=bool, 
#               required=False, 
#               help='If checked, returns license of the package.')
@click.option('--pip-version', 
              'get_pip_version', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns pip latest version of the package.')
# @click.option('--paa-version', 
#               'get_paa_version', 
#               is_flag=True, 
#               type=bool, 
#               required=False, 
#               help='If checked, returns packaging tool version with which the package was packaged.')
@click.pass_context
def show_module_info(ctx,
        label_name,
        #get_paa_cli_status,
        get_keywords,
        get_classifiers,
        get_docstring,
        get_author,
        get_author_email,
        get_version,
        get_pip_version,
        #get_paa_version,
        get_license_label,
        #get_license
        ):
    """Shows module info."""

    package_mapping = {'PIL': 'Pillow',
                        'bs4': 'beautifulsoup4',
                        'fitz': 'PyMuPDF',
                        'attr': 'attrs',
                        'dotenv': 'python-dotenv',
                        'googleapiclient': 'google-api-python-client',
                        'google_auth_oauthlib': 'google-auth-oauthlib',
                        'sentence_transformers': 'sentence-transformers',
                        'flask': 'Flask',
                        'stdlib_list': 'stdlib-list',
                        'sklearn': 'scikit-learn',
                        'yaml': 'pyyaml',
                        'package_auto_assembler': 'package-auto-assembler',
                        'git': 'gitpython'}

    import_name = [key for key,value in package_mapping.items() \
        if value == label_name]

    if len(import_name)>0:
        import_name = import_name[0]
    else:
        import_name = label_name

    try:
        package = importlib.import_module(import_name.replace('-','_'))
    except ImportError:
        click.echo(f"No package with name {label_name} was installed or mapping does not support it!")

    da = DependenciesAnalyser()

    try:
        package_metadata = da.get_package_metadata(label_name)
    except Exception:
        click.echo(f"Failed to extract {label_name} metadata!")

    # get docstring
    try:
        docstring = package.__doc__
    except ImportError:
        docstring = None

    try:
        vh_params = {
        'versions_filepath' : '',
        'log_filepath' : '',
        'read_files' : False,
        'default_version' : "0.0.0"
        }

        vh = VersionHandler(**vh_params)

        latest_version = vh.get_latest_pip_version(label_name)
    except Exception as e:
        latest_version = None

    if not any([get_version, 
                get_pip_version,
                #get_paa_version,
                get_author, 
                get_author_email, 
                get_docstring,
                get_classifiers,
                get_keywords,
                #get_paa_cli_status,
                #get_license,
                get_license_label]):

        if docstring:
            click.echo(docstring)

        if package_metadata.get('version'):
            click.echo(f"Installed version: {package_metadata.get('version')}")

        if latest_version:
            click.echo(f"Latest pip version: {latest_version}")
        
        # if package_metadata.get('paa_version'):
        #     click.echo(f"Packaged with PAA version: {package_metadata.get('paa_version')}")
        
        # if package_metadata.get('paa_cli'):
        #     click.echo(f"Is cli interface available: {package_metadata.get('paa_cli')}")

        if package_metadata.get('author'):
            click.echo(f"Author: {package_metadata.get('author')}")

        if package_metadata.get('author_email'):
            click.echo(f"Author-email: {package_metadata.get('author_email'):}")

        if package_metadata.get('keywords'):
            click.echo(f"Keywords: {package_metadata.get('keywords')}")

        if package_metadata.get('license_label'):
            click.echo(f"License: {package_metadata.get('license_label')}")

        if package_metadata.get('classifiers'):
            click.echo(f"Classifiers: {package_metadata.get('classifiers')}")
    
    if get_version:
        click.echo(package_metadata.get('version'))
    if get_pip_version:
        click.echo(latest_version)
    # if get_paa_version:
    #     click.echo(package_metadata.get('paa_version'))
    if get_author:
        click.echo(package_metadata.get('author'))
    if get_author_email:
        click.echo(package_metadata.get('author_email'))
    if get_docstring:
        click.echo(docstring)
    if get_classifiers:
        for cl in package_metadata.get('classifiers'):
            click.echo(f"{cl}")
    if get_keywords:
        for kw in package_metadata.get('keywords'):
            click.echo(f"{kw}")
    # if get_paa_cli_status:
    #     click.echo(package_metadata.get('paa_cli'))
    if get_license_label:
        click.echo(package_metadata.get('license_label'))
    # if get_license:
    #     click.echo(license_text)


@click.command()
@click.argument('label_name')
@click.pass_context
def show_module_requirements(ctx,
        label_name):
    """Shows module requirements."""

    da = DependenciesAnalyser()

    label_name = label_name.replace('-','_')
    requirements = da.get_package_requirements(label_name)
    
    for req in requirements:
        click.echo(f"{req}")

@click.command()
@click.argument('package_name')
@click.option('--normalize-labels', 
              'normalize_labels', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, package license labels are normalized.')
@click.pass_context
def show_module_licenses(ctx,
        package_name,
        normalize_labels):
    """Shows module licenses."""

    da = DependenciesAnalyser(loggerLvl = logging.INFO)
    
    package_name = package_name.replace('-','_')

    if normalize_labels:
        normalize_labels = True
    else:
        normalize_labels = False
    

    extracted_dependencies_tree = da.extract_dependencies_tree(
        package_name = package_name
    )

    extracted_dependencies_tree_license = da.add_license_labels_to_dep_tree(
        dependencies_tree = extracted_dependencies_tree,
        normalize = normalize_labels
    )

    da.print_flattened_tree(extracted_dependencies_tree_license)

@click.command()
@click.option('--api-config','api_config', type=str, 
             default=".paa.api.config",
             required=False, 
             help='Path to yml config file with app description, middleware parameters, run parameters, `.paa.api.config` is used by default.')
@click.option('--host', default=None, help='The host to bind to.')
@click.option('--port', default=None, help='The port to bind to.')
@click.option('--package', 
              'package_names',
              multiple=True,
              required=False, 
              help='Package names from which routes will be added to the app.')
@click.option('--route', 
              'routes_paths', 
              multiple=True, 
              required=False, 
              help='Paths to routes which will be added to the app.')
@click.option('--docs', 
              'docs_paths', 
              multiple=True, 
              required=False, 
              help='Paths to static docs site which will be added to the app.')
@click.pass_context
def run_api_routes(ctx,
        api_config,
        package_names,
        routes_paths,
        docs_paths,
        host,
        port):
    """Run fastapi with provided routes."""

    if os.path.exists(api_config):
        with open(api_config, 'r') as file:
            api_config = yaml.safe_load(file)
    else:
        api_config = {}

    description_config = api_config.get('DESCRIPTION')
    middleware_config = api_config.get('MIDDLEWARE')
    run_config = api_config.get('RUN')

    if run_config is None:
        run_config = {}

    if host:
        run_config['host'] = host

    if port:
        run_config['port'] = port
    

    fah = FastApiHandler(loggerLvl = logging.INFO)
    
    fah.run_app(
        description = description_config,
        middleware = middleware_config,
        run_parameters = run_config,
        package_names = package_names,
        routes_paths = routes_paths,
        docs_paths = docs_paths
    )

@click.command()
@click.option('--app-config','app_config', type=str, 
             default=".paa.streamlit.config",
             required=False, 
             help='Path to yml config for streamlit app.')
@click.option('--host', default=None, help='The host to bind to.')
@click.option('--port', default=None, help='The port to bind to.')
@click.option('--package', 
              'package_name',
              required=False, 
              help='Package name from which streamlit app should be run.')
@click.option('--path', 
              'streamlit_filepath',
              required=False, 
              help='Path to streamlit app.')
@click.pass_context
def run_streamlit(ctx,
        app_config,
        package_name,
        streamlit_filepath,
        host,
        port):
    """Run streamlit application from the package."""


    sh = StreamlitHandler(loggerLvl = logging.INFO)
    
    sh.run_app(
        package_name = package_name,
        streamlit_filepath = streamlit_filepath,
        config_path = app_config,
        host = host,
        port = port
    )

@click.command()
@click.argument('package_name')
@click.option('--output-dir', 
              'output_dir', 
              type=str, required=False, 
              help='Directory where routes extracted from the package will be copied to.')
@click.option('--output-path', 
              'output_path', 
              type=str, required=False, 
              help='Filepath to which routes extracted from the package will be copied to.')
@click.pass_context
def extract_module_routes(ctx,
        package_name,
        output_dir,
        output_path):
    """Extracts routes for fastapi from packages that have them into a file."""

    fah = FastApiHandler(loggerLvl = logging.INFO)

    fah.extract_routes_from_package(
        package_name = package_name.replace("-", "_"), 
        output_directory = output_dir, 
        output_filepath = output_path
    )

@click.command()
@click.argument('package_name')
@click.option('--output-dir', 
              'output_dir', 
              type=str, required=False, 
              help='Directory where streamplit extracted from the package will be copied to.')
@click.option('--output-path', 
              'output_path', 
              type=str, required=False, 
              help='Filepath to which streamlit extracted from the package will be copied to.')
@click.pass_context
def extract_module_streamlit(ctx,
        package_name,
        output_dir,
        output_path):
    """Extracts streamlit from packages that have them into a file."""

    sh = StreamlitHandler(loggerLvl = logging.INFO)

    sh.extract_streamlit_from_package(
        package_name = package_name.replace("-", "_"), 
        output_directory = output_dir, 
        output_filepath = output_path
    )

@click.command()
@click.argument('package_name')
@click.option('--artifact', 
              type=str, required=False, 
              help='Name of the artifact to be extracted.')
@click.option('--output-dir', 
              'output_dir', 
              type=str, required=False, 
              help='Directory where artifacts extracted from the package will be copied to.')
@click.option('--output-path', 
              'output_path', 
              type=str, required=False, 
              help='Filepath to which artifact extracted from the package will be copied to.')
@click.pass_context
def extract_module_artifacts(ctx,
        package_name,
        artifact,
        output_dir,
        output_path):
    """Extracts artifacts from packaged module."""

    ah = ArtifactsHandler(
        module_name = package_name.replace('-','_')
    )

    package_artifacts = ah.get_packaged_artifacts()


    if artifact:

        if output_dir is None:
            output_dir = '.'

        if output_path is None:
            output_path = os.path.join(output_dir, artifact)

        if artifact in package_artifacts.keys():
            shutil.copy(package_artifacts[artifact], output_path)
        else:
            click.echo(f"Artifact {artifact} was not found in {package_name}!")
    else:

        destination = 'artifacts'

        if output_dir:
            destination = output_dir
        if output_path:
            destination = output_path

        with pkg_resources.path(f"{package_name.replace('-','_')}", 
            'artifacts') as path:
                artifacts_filepath = path

        if os.path.exists(artifacts_filepath):
            shutil.copytree(artifacts_filepath, destination)
        else:
            click.echo(f"Artifacts were not found in {package_name}!")

@click.command()
@click.argument('package_name')
@click.option('--output-dir', 
              'output_dir', 
              type=str, required=False, 
              help='Directory where routes extracted from the package will be copied to.')
@click.option('--output-path', 
              'output_path', 
              type=str, required=False, 
              help='Filepath to which routes extracted from the package will be copied to.')
@click.pass_context
def extract_module_site(ctx,
        package_name,
        output_dir,
        output_path):
    """Extracts static mkdocs site from packaged module."""

    destination = 'mkdocs'

    if output_dir:
        destination = output_dir
    if output_path:
        destination = output_path

    with pkg_resources.path(f"{package_name.replace('-','_')}", 
            'mkdocs') as path:
                mkdocs_filepath = path

    if os.path.exists(mkdocs_filepath):
        shutil.copytree(mkdocs_filepath, destination)
    else:
        click.echo(f"Mkdocs static page was not found in {package_name}!")

@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.pass_context
def extract_module_requirements(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        dependencies_dir):
    """Extract module requirements."""

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
        "check_vulnerabilities" : False,
        "add_artifacts" : False
    }

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("python_version"):
        paa_params["python_version"] = test_install_config["python_version"]

    if test_install_config.get("kernel_name"):
        paa_params["kernel_name"] = test_install_config["kernel_name"]

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

            requirements_list = paa.requirements_list + paa.optional_requirements_list

            for req in requirements_list:
                click.echo(req)

        except Exception as e:
            print("")
        finally:
            shutil.rmtree(paa.setup_directory)

    else:
        paa.logger.info(f"Metadata condition was not fullfield for {module_name.replace('_','-')}")

@click.command()
@click.argument('label_name')
@click.pass_context
def show_module_artifact_links(ctx,
        label_name):
    """Shows module artifact links."""

    ah = ArtifactsHandler(
        module_name = label_name.replace('-','_'))

    link_for_artifacts, link_availability = ah.show_module_links()

    if link_for_artifacts:

        artifact_names = [a.replace(".link","") for a,l in link_for_artifacts.items()]
        artifact_links = [l for a,l in  link_for_artifacts.items()]
        link_availabilities = [la for a,la in  link_availability.items()]

        # Calculate the maximum length of package names for formatting
        max_name_length = max(len(a) for a in artifact_names) if artifact_names else 0
        max_link_length = max(len(l) for l in artifact_links) if artifact_links else 0
        max_link_a_length = max(len(str(la)) for la in link_availabilities) if link_availabilities else 0
        
        # Print the header
        header_name = "Artifact"
        header_link = "Link"
        header_availability = "Available"

        click.echo(f"{header_name:<{max_name_length}} {header_link:<{max_link_length}} {header_availability:<{max_link_a_length}}")
        click.echo(f"{'-' * max_name_length} {'-' * max_link_length} {'-' * max_link_a_length}")

        # Print each package and its version
        for artifact, link in link_for_artifacts.items():
            available = link_availability[artifact]
            artifact = artifact.replace(".link","")
            click.echo(f"{artifact:<{max_name_length}} {link:<{max_link_length}} {str(available):<{max_link_a_length}}")
    
    else:
        click.echo(f"No link for package artifacts found for {label_name}!")

@click.command()
@click.argument('label_name')
@click.pass_context
def refresh_module_artifacts(ctx,
        label_name):
    """Refreshes module artifact from links."""

    ah = ArtifactsHandler(
        module_name = label_name.replace('-','_'))

    failed_refreshes = ah.refresh_artifacts_from_link()

    link_for_artifacts, _ = ah.show_module_links()

    click.echo(f"{len(link_for_artifacts) - failed_refreshes} links refreshed for {label_name}")


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.pass_context
def extract_tracking_version(ctx,
        config,
        module_name):
    """Get latest package version."""


    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    MAPPING_FILE = test_install_config['mapping_filepath']
    VERSIONS_FILE = test_install_config['versions_filepath']

    # if os.path.exists(MAPPING_FILE):

    #     with open(MAPPING_FILE, 'r') as file:
    #         # Load the contents of the file
    #         mapping_file = yaml.safe_load(file) or {}

    #     module_name = mapping_file.get(module_name, module_name)

    module_version = "0.0.0"
    if os.path.exists(VERSIONS_FILE):

        with open(VERSIONS_FILE, 'r') as file:
            # Load the contents of the file
            versions_file = yaml.safe_load(file) or {}

        module_version = versions_file.get(module_name, 
            test_install_config.get("default_version", "0.0.0"))
    
    click.echo(module_version)
    

cli.add_command(init_paa, "init-paa")
cli.add_command(init_config, "init-config")
cli.add_command(test_install, "test-install")
cli.add_command(make_package, "make-package")
cli.add_command(check_vulnerabilities, "check-vulnerabilities")
cli.add_command(check_licenses, "check-licenses")
cli.add_command(update_release_notes, "update-release-notes")
cli.add_command(run_api_routes, "run-api-routes")
cli.add_command(run_streamlit, "run-streamlit")
cli.add_command(show_module_list, "show-module-list")
cli.add_command(show_module_info, "show-module-info")
cli.add_command(show_module_requirements, "show-module-requirements")
cli.add_command(show_module_licenses, "show-module-licenses")
cli.add_command(show_module_artifacts, "show-module-artifacts")
cli.add_command(show_module_artifact_links, "show-module-artifacts-links")
cli.add_command(refresh_module_artifacts, "refresh-module-artifacts")
cli.add_command(extract_tracking_version, "extract-tracking-version")
cli.add_command(extract_module_routes, "extract-module-routes")
cli.add_command(extract_module_streamlit, "extract-module-streamlit")
cli.add_command(extract_module_artifacts, "extract-module-artifacts")
cli.add_command(extract_module_requirements, "extract-module-requirements")
cli.add_command(extract_module_site, "extract-module-site")


if __name__ == "__main__":
    cli()

