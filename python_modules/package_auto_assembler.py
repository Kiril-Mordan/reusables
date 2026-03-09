"""
`package-auto-assembler` is a tool designed to streamline creation of `single module packages`.
Its primary goal is to automate as many aspects of python package creation as possible,
thereby shortening the development cycle of reusable components and maintaining a high standard of quality for reusable code.

With `package-auto-assembler`, you can simplify the package creation process to the point where it can be seamlessly triggered within CI/CD pipelines, requiring minimal setup and preparation for new modules.

## Key features

- [Set up new Python packaging repositories](https://kiril-mordan.github.io/reusables/package_auto_assembler/python_packaging_repo/) for Github and Azure DevOps.
- [Create and validate packages](https://kiril-mordan.github.io/reusables/package_auto_assembler/cli/) with `make-package` and `test-install`.
- [Check module dependencies](https://kiril-mordan.github.io/reusables/package_auto_assembler/dependency_management/) for vulnerabilities, compatibility, and license constraints.
- [Run and expose interfaces](https://kiril-mordan.github.io/reusables/package_auto_assembler/mcp/) through MCP, and via [FastAPI](https://kiril-mordan.github.io/reusables/package_auto_assembler/fastapi/) or [Streamlit](https://kiril-mordan.github.io/reusables/package_auto_assembler/interfaces/streamlit/) integrations.
- [Extract artifacts and files](https://kiril-mordan.github.io/reusables/package_auto_assembler/artifacts/) packaged alongside code.
- [Show detailed module information](https://kiril-mordan.github.io/reusables/package_auto_assembler/cli/) for installed packages built with PAA.
- [Create and navigate package history checkpoints](https://kiril-mordan.github.io/reusables/package_auto_assembler/checkpoint_history/) including list/show/prune/checkout flows.

"""

import logging
import os
import sys
import subprocess
import shutil
import copy
import importlib
import importlib.metadata
import attrs #>=22.2.0
import attrsx

from .components.paa_deps.artifacts_handler import ArtifactsHandler
from .components.paa_deps.cli_handler import CliHandler
from .components.paa_deps.drawio_handler import DrawioHandler
from .components.paa_deps.dependencies_analyzer import DependenciesAnalyser
from .components.paa_deps.fastapi_handler import FastApiHandler
from .components.paa_deps.streamlit_handler import StreamlitHandler
from .components.paa_deps.mcp_handler import McpHandler
from .components.paa_deps.import_mapping_handler import ImportMappingHandler
from .components.paa_deps.local_dependencies_handler import LocalDependaciesHandler
from .components.paa_deps.long_doc_handler import LongDocHandler
from .components.paa_deps.metadata_handler import MetadataHandler
from .components.paa_deps.mkdocs_handler import MkDocsHandler
from .components.paa_deps.release_notes_handler import ReleaseNotesHandler
from .components.paa_deps.requirements_handler import RequirementsHandler
from .components.paa_deps.setup_dir_handler import SetupDirHandler
from .components.paa_deps.skills_handler import SkillsHandler
from .components.paa_deps.checkpoint_handler import CheckpointHandler
from .components.paa_deps.version_handler import VersionHandler
from .components.paa_deps.ppr_handler import PprHandler, PAA_PATH_DEFAULTS
from .components.paa_deps.tests_handler import TestsHandler

#@ numpy==1.26.0
#@ setuptools>=78.1.1
#@ wheel>=0.44.0
#@ twine>=5.1.1

__package_metadata__ = {
    "author": "Kyrylo Mordan",
    "author_email": "parachute.repo@gmail.com",
    "description": "A tool to automate package creation within ci based on just .py and optionally .ipynb file.",
    "keywords" : ['python', 'packaging'],
    "url" : 'https://kiril-mordan.github.io/reusables/package_auto_assembler/',
    "classifiers" : ["Development Status :: 5 - Production/Stable"]
}

@attrsx.define(
    handler_specs={
        "setup_dir": SetupDirHandler,
        "version": VersionHandler,
        "import_mapping": ImportMappingHandler,
        "local_dependacies": LocalDependaciesHandler,
        "requirements": RequirementsHandler,
        "metadata": MetadataHandler,
        "long_doc": LongDocHandler,
        "cli": CliHandler,
        "release_notes": ReleaseNotesHandler,
        "dependencies_analyzer": DependenciesAnalyser,
        "fastapi": FastApiHandler,
        "artifacts": ArtifactsHandler,
        "mkdocs": MkDocsHandler,
        "drawio": DrawioHandler,
        "ppr": PprHandler,
        "skills": SkillsHandler,
        "checkpoint": CheckpointHandler,
        "tests": TestsHandler,
        "streamlit": StreamlitHandler,
        "mcp": McpHandler,
    },
    logger_chaining={
        "logger": True
    }
)
class PackageAutoAssembler:
    # pylint: disable=too-many-instance-attributes

    ## inputs
    module_name = attrs.field(type=str)
    module_filepath = attrs.field(type=str)

    ## paths
    cli_module_filepath = attrs.field(default=None)
    fastapi_routes_filepath = attrs.field(default=None)
    mcp_module_filepath = attrs.field(default=None)
    mapping_filepath = attrs.field(default=".paa/package_mapping.json")
    licenses_filepath = attrs.field(default=".paa/package_licenses.json")
    allowed_licenses = attrs.field(default=['mit', 'apache-2.0', 'lgpl-3.0',
                            'bsd-3-clause', 'bsd-2-clause', '-', 'mpl-2.0'])
    example_notebook_path = attrs.field(default=None)
    versions_filepath = attrs.field(default='.paa/tracking/lsts_package_versions.yml')
    log_filepath = attrs.field(default='.paa/tracking/version_logs.csv')
    setup_directory = attrs.field(default='./setup_dir')
    release_notes_filepath = attrs.field(default=None)
    config_filepath = attrs.field(default=".paa.config")
    cli_docs_filepath = attrs.field(default=None)
    drawio_filepath = attrs.field(default=None)
    streamlit_filepath = attrs.field(default=None)

    module_dir = attrs.field(default=None)
    paa_dir = attrs.field(default="./.paa")
    docs_path = attrs.field(default="./.paa/docs")
    drawio_dir = attrs.field(default=None)
    tests_dir = attrs.field(default=None)
    artifacts_dir = attrs.field(default=None)
    dependencies_dir = attrs.field(default=None)
    extra_docs_dir = attrs.field(default=None)
    pyproject_dir = attrs.field(default="./.paa/pyproject")

    # optional parameters
    pylint_threshold = attrs.field(default=None)
    classifiers = attrs.field(default=['Development Status :: 3 - Alpha'])
    license_path = attrs.field(default=None)
    notice_path = attrs.field(default=None)
    license_label = attrs.field(default=None)
    license_badge = attrs.field(default=None)
    docs_url = attrs.field(default=None)
    source_repo_url = attrs.field(default=None)
    source_repo_name = attrs.field(default=None)
    requirements_list = attrs.field(default=[])
    optional_requirements_list = attrs.field(default=[])
    python_version = attrs.field(default="3.10")
    version_increment_type = attrs.field(default="patch", type = str)
    default_version = attrs.field(default="0.0.0", type = str)
    kernel_name = attrs.field(default = 'python', type = str)
    max_git_search_depth = attrs.field(default=5, type = int)
    artifacts_filepaths = attrs.field(default=None, type = dict)
    docs_file_paths = attrs.field(default=None, type = dict)

    # switches
    add_artifacts = attrs.field(default=True, type = bool)
    remove_temp_files = attrs.field(default=True, type = bool)
    skip_deps_install = attrs.field(default=False, type = bool)
    check_vulnerabilities = attrs.field(default=True, type = bool)
    check_dependencies_compatibility = attrs.field(default=True, type = bool)
    check_full_dependencies_compatibility = attrs.field(default=False, type = bool)
    add_requirements_header = attrs.field(default=True, type = bool)
    use_commit_messages = attrs.field(default=True, type = bool)
    check_dependencies_licenses = attrs.field(default=False, type = bool)
    execute_readme_notebook = attrs.field(default=True, type = bool)
    add_mkdocs_site = attrs.field(default=True, type = bool)

    ## output
    original_module_filepath = attrs.field(default = None)
    local_dependacies_list = attrs.field(default = None)
    version = attrs.field(default=None)
    metadata = attrs.field(default={})
    custom_modules_list = attrs.field(default=[], type=list)
    cli_metadata = attrs.field(default={}, type = dict)
    add_cli_tool = attrs.field(default = None, type = bool)
    package_result = attrs.field(init=False)


    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Package Auto Assembler')
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

    def __attrs_post_init__(self):
        self._initialize_metadata_h(params={
            "module_filepath": self.module_filepath,
            "logger": self.logger
        })
        self._initialize_import_mapping_h(params={
            "mapping_filepath": self.mapping_filepath,
            "logger": self.logger
        })
        self._initialize_checkpoint_h(params={
            "path_defaults": copy.deepcopy(PAA_PATH_DEFAULTS),
            "get_module_deps_paths": (
                lambda main_module_filepath, dependencies_dir: LocalDependaciesHandler(
                    main_module_filepath=main_module_filepath,
                    dependencies_dir=dependencies_dir,
                    logger=self.logger
                ).get_module_deps_path()
            ),
            "logger": self.logger
        })
        self.original_module_filepath = self.module_filepath

    def _add_requirements(self,
                            module_filepath : str = None,
                            custom_modules : list = None,
                            import_mappings : str = None,
                            check_vulnerabilities : bool = None,
                            check_dependencies_compatibility : bool = None,
                            check_full_dependencies_compatibility : bool = None,
                            check_dependencies_licenses : bool = None,
                            add_header : bool = None):

        """
        Extract and add requirements.
        """

        if self.requirements_h is None:
            self._initialize_requirements_h(params={
                "module_filepath": self.module_filepath,
                "custom_modules_filepath": self.dependencies_dir,
                "python_version": self.python_version,
                "logger": self.logger
            })
        if module_filepath is None:
            module_filepath = self.module_filepath

        if check_vulnerabilities is None:
            check_vulnerabilities = self.check_vulnerabilities

        if check_dependencies_compatibility is None:
            check_dependencies_compatibility = self.check_dependencies_compatibility

        if check_full_dependencies_compatibility is None:
            check_full_dependencies_compatibility = self.check_full_dependencies_compatibility

        if check_dependencies_licenses is None:
            check_dependencies_licenses = self.check_dependencies_licenses

        if import_mappings is None:
            import_mappings = self.import_mapping_h.load_package_mappings()

        if add_header is None:
            add_header = self.add_requirements_header

        custom_modules_list = self.requirements_h.list_custom_modules()

        if custom_modules:
            custom_modules_list += custom_modules

        self.logger.debug(f"Adding requirements from {module_filepath}")

        # extracting package requirements
        self.requirements_h.extract_requirements(
            package_mappings=import_mappings,
            module_filepath=module_filepath,
            custom_modules=custom_modules_list,
            add_header = add_header)

        self.requirements_list = self.requirements_h.requirements_list
        self.optional_requirements_list = self.requirements_h.optional_requirements_list

        if check_dependencies_compatibility:
            self.requirements_h.check_requirements_compatibility(
                requirements_list=self.requirements_list + self.optional_requirements_list
            )

        if check_full_dependencies_compatibility:
            self.requirements_h.check_full_requirements_compatibility(
                requirements_list=self.requirements_list + self.optional_requirements_list
            )

        if check_vulnerabilities:
            self.requirements_h.check_vulnerabilities()

        if check_dependencies_licenses:
            if self.dependencies_analyzer_h is None:
                self._initialize_dependencies_analyzer_h(params={
                    "package_licenses_filepath": self.licenses_filepath,
                    "allowed_licenses": self.allowed_licenses,
                    "logger": self.logger
                })
                edt = self.dependencies_analyzer_h.extract_dependencies_tree(
                    requirements = self.requirements_list + self.optional_requirements_list
                )

                edtl = self.dependencies_analyzer_h.add_license_labels_to_dep_tree(
                    dependencies_tree = edt
                )

                self.dependencies_analyzer_h.find_unexpected_licenses_in_deps_tree(
                    tree_dep_license = edtl
                )

    ###

    def initialize_paa_dir(self, paa_dir : str = None):

        """
        Initialize paa dir
        """

        if self.ppr_h is None:
            self._initialize_ppr_h(params={
                "paa_dir": self.paa_dir,
                "drawio_dir": self.drawio_dir,
                "docs_dir": self.docs_path,
                "module_dir": self.module_dir,
                "pylint_threshold": self.pylint_threshold,
                "logger": self.logger
            })
        self.ppr_h.init_paa_dir(
            paa_dir = paa_dir)


    def add_metadata_from_module(self, module_filepath : str = None):

        """
        Add metadata extracted from the module.
        """

        self.logger.debug(f"Adding metadata ...")

        if self.metadata_h is None:
            self._initialize_metadata_h(params={
                "module_filepath": self.module_filepath,
                "logger": self.logger
            })
        if module_filepath is None:
            module_filepath = self.module_filepath

        # extracting package metadata
        self.metadata = self.metadata_h.get_package_metadata(
            module_filepath = module_filepath)


    def add_metadata_from_cli_module(self,
                                     cli_module_filepath : str = None):

        """
        Add metadata extracted from the cli module.
        """

        self.logger.debug(f"Adding cli metadata ...")

        if self.metadata_h is None:
            self._initialize_metadata_h(params={
                "module_filepath": self.module_filepath,
                "logger": self.logger
            })
        if cli_module_filepath is None:
            cli_module_filepath = self.cli_module_filepath

        if os.path.exists(cli_module_filepath) \
            and os.path.isfile(cli_module_filepath) \
                and self.metadata_h.is_metadata_available(
                    module_filepath = cli_module_filepath,
                    header_name = "__cli_metadata__"):

            # extracting package metadata
            self.cli_metadata = self.metadata_h.get_package_metadata(
                module_filepath = cli_module_filepath,
                header_name = "__cli_metadata__")



    def add_or_update_version(self,
                              module_name : str = None,
                              version_increment_type : str = None,
                              version : str = None,
                              versions_filepath : str = None,
                              log_filepath : str = None,
                              use_commit_messages : bool = None):

        """
        Increment version and creates entry in version logs.
        """

        self.logger.debug(f"Incrementing version ...")

        if self.version_h is None:
            self._initialize_version_h(params={
                "versions_filepath": self.versions_filepath,
                "log_filepath": self.log_filepath,
                "default_version": self.default_version,
                "logger": self.logger
            })
        if use_commit_messages is None:
            use_commit_messages = self.use_commit_messages

        if use_commit_messages:
            self._initialize_release_notes_h(params={
                "filepath": self.release_notes_filepath,
                "label_name": self.module_name,
                "version": version if version is not None else self.default_version,
                "max_search_depth": self.max_git_search_depth,
                "logger": self.logger
            })
            self.release_notes_h.extract_version_update()

            version_increment_type = self.release_notes_h.version_update_label

            if self.release_notes_h.version != self.default_version:
                version = self.release_notes_h.version

        else:
            version_increment_type = None


        if module_name is None:
            module_name = self.module_name

        if version_increment_type is None:
            version_increment_type = self.version_increment_type

        if versions_filepath is None:
            versions_filepath = self.versions_filepath

        if log_filepath is None:
            log_filepath = self.log_filepath


        self.version_h.increment_version(package_name = module_name,
                                         version = version,
                                        increment_type = version_increment_type,
                                        default_version = version)
        version = self.version_h.get_version(package_name=module_name)

        self.metadata['version'] = version
        if self.release_notes_filepath:
            self.release_notes_h.version = self.metadata['version']

    def add_or_update_release_notes(self,
                              filepath : str = None,
                              version : str = None):

        """
        Increment version and creates entry in version logs.
        """

        self.logger.debug(f"Updating release notes ...")

        if self.release_notes_h is None:
            self._initialize_release_notes_h(params={
                "filepath": self.release_notes_filepath,
                "label_name": self.module_name,
                "version": self.default_version,
                "max_search_depth": self.max_git_search_depth,
                "logger": self.logger
            })
        if filepath:
            self.release_notes_h.filepath = filepath
            self.release_notes_h._initialize_notes()

        if version:
            self.release_notes_h.version = version

        self.release_notes_h.create_release_note_entry()
        self.release_notes_h.save_release_notes()

    def prep_setup_dir(self,
                       module_filepath : str = None,
                       module_docstring : str = None):

        """
        Prepare setup directory.
        """

        self.logger.debug(f"Preparing setup directory ...")

        if self.setup_dir_h is None:
            self._initialize_setup_dir_h(params={
                "module_name": self.module_name,
                "module_filepath": self.module_filepath,
                "setup_directory": self.setup_directory,
                "pyproject_directory": self.pyproject_dir,
                "license_path": self.license_path,
                "notice_path": self.notice_path,
                "license_label": self.license_label,
                "docs_url": self.docs_url,
                "version": self.metadata.get("version"),
                "logger": self.logger
            })
        if module_filepath is None:
            module_filepath = self.module_filepath

        if module_docstring is None:

            if self.long_doc_h is None:
                self._initialize_long_doc_h(params={
                    "module_name": self.module_name,
                    "notebook_path": self.example_notebook_path,
                    "kernel_name": self.kernel_name,
                    "logger": self.logger
                })
            module_content = self.long_doc_h.read_module_content(filepath = module_filepath)

            module_docstring = self.long_doc_h.extract_module_docstring(module_content = module_content)

        # add module docstring
        self.setup_dir_h.docstring = module_docstring
        # create empty dir for setup
        self.setup_dir_h.flush_n_make_setup_dir()
        # copy module to dir
        self.setup_dir_h.copy_module_to_setup_dir()
        # copy license to dir
        self.setup_dir_h.copy_license_to_setup_dir()
        # copy notice to dir
        self.setup_dir_h.copy_notice_to_setup_dir()
        # create init file for new package
        self.setup_dir_h.create_init_file()


    def merge_local_dependacies(self,
                                main_module_filepath : str = None,
                                dependencies_dir : str = None,
                                save_filepath : str = None):

        """
        Combine local dependacies and main module into one file.
        """

        if self.local_dependacies_h is None:
            self._initialize_local_dependacies_h(params={
                "main_module_filepath": self.module_filepath,
                "dependencies_dir": self.dependencies_dir,
                "logger": self.logger
            })
        if main_module_filepath is None:
            main_module_filepath = self.module_filepath

        if dependencies_dir is None:
            dependencies_dir = self.dependencies_dir

        if save_filepath is None:
            save_filepath = os.path.join(self.setup_directory, os.path.basename(main_module_filepath))

        if dependencies_dir:
            self.logger.debug(f"Merging {main_module_filepath} with dependecies from {dependencies_dir} into {save_filepath}")

            # combime module with its dependacies
            self.local_dependacies_h.save_combined_modules(
                combined_module=self.local_dependacies_h.combine_modules(main_module_filepath = main_module_filepath,
                                                                        dependencies_dir = dependencies_dir),
                save_filepath=save_filepath
            )

            # switch filepath for the combined one
            self.module_filepath = save_filepath
            self.local_dependacies_list = self.local_dependacies_h.filtered_dep_names_list


    def add_requirements_from_module(self,
                                     module_filepath : str = None,
                                     custom_modules : list = None,
                                     import_mappings : str = None,
                                     check_vulnerabilities : bool = None,
                                     check_dependencies_compatibility : bool = None,
                                     check_full_dependencies_compatibility : bool = None,
                                     check_dependencies_licenses : bool = None,
                                     add_header : bool = None):

        """
        Extract and add requirements from the module.
        """

        self._add_requirements(
            module_filepath = module_filepath,
            custom_modules = custom_modules,
            import_mappings = import_mappings,
            check_vulnerabilities = check_vulnerabilities,
            check_dependencies_compatibility = check_dependencies_compatibility,
            check_full_dependencies_compatibility = check_full_dependencies_compatibility,
            check_dependencies_licenses = check_dependencies_licenses,
            add_header = add_header
        )

    def add_requirements_from_cli_module(self,
                                     module_name : str = None,
                                     cli_module_filepath : str = None,
                                     custom_modules : list = None,
                                     import_mappings : str = None,
                                     check_vulnerabilities : bool = None,
                                     check_dependencies_compatibility : bool = None,
                                     check_full_dependencies_compatibility : bool = None,
                                     check_dependencies_licenses : bool = None):

        """
        Extract and add requirements from the module.
        """

        if cli_module_filepath is None:
            cli_module_filepath = self.cli_module_filepath

        if module_name is None:
            module_name = self.module_name

        if custom_modules is None:
            custom_modules = []

        if cli_module_filepath \
            and os.path.exists(cli_module_filepath) \
                and os.path.isfile(cli_module_filepath):

            self._add_requirements(
                module_filepath = cli_module_filepath,
                custom_modules = custom_modules + [module_name],
                import_mappings = import_mappings,
                check_vulnerabilities = check_vulnerabilities,
                check_dependencies_compatibility = check_dependencies_compatibility,
                check_full_dependencies_compatibility = check_full_dependencies_compatibility,
                check_dependencies_licenses = check_dependencies_licenses,
                add_header = False
            )

    def add_requirements_from_api_route(self,
                                     module_name : str = None,
                                     fastapi_routes_filepath : str = None,
                                     custom_modules : list = None,
                                     import_mappings : str = None,
                                     check_vulnerabilities : bool = None,
                                     check_dependencies_compatibility : bool = None,
                                     check_full_dependencies_compatibility : bool = None,
                                     check_dependencies_licenses : bool = None):

        """
        Extract and add requirements from the module.
        """

        if fastapi_routes_filepath is None:
            fastapi_routes_filepath = self.fastapi_routes_filepath

        if module_name is None:
            module_name = self.module_name

        if custom_modules is None:
            custom_modules = []

        if (fastapi_routes_filepath is not None) and \
            os.path.exists(fastapi_routes_filepath) \
                and os.path.isfile(fastapi_routes_filepath):

            self._add_requirements(
                module_filepath = fastapi_routes_filepath,
                custom_modules = custom_modules + [module_name],
                import_mappings = import_mappings,
                check_vulnerabilities = check_vulnerabilities,
                check_dependencies_compatibility = check_dependencies_compatibility,
                check_full_dependencies_compatibility = check_full_dependencies_compatibility,
                check_dependencies_licenses = check_dependencies_licenses,
                add_header = False
            )

    def add_requirements_from_streamlit(self,
                                     module_name : str = None,
                                     streamlit_filepath : str = None,
                                     custom_modules : list = None,
                                     import_mappings : str = None,
                                     check_vulnerabilities : bool = None,
                                     check_dependencies_compatibility : bool = None,
                                     check_full_dependencies_compatibility : bool = None,
                                     check_dependencies_licenses : bool = None):

        """
        Extract and add requirements from the module.
        """

        if streamlit_filepath is None:
            streamlit_filepath = self.streamlit_filepath

        if module_name is None:
            module_name = self.module_name

        if custom_modules is None:
            custom_modules = []

        if (streamlit_filepath is not None) and \
            os.path.exists(streamlit_filepath) \
                and os.path.isfile(streamlit_filepath):

            self._add_requirements(
                module_filepath = streamlit_filepath,
                custom_modules = custom_modules + [module_name],
                import_mappings = import_mappings,
                check_vulnerabilities = check_vulnerabilities,
                check_dependencies_compatibility = check_dependencies_compatibility,
                check_full_dependencies_compatibility = check_full_dependencies_compatibility,
                check_dependencies_licenses = check_dependencies_licenses,
                add_header = False
            )

    def add_requirements_from_mcp(self,
                                  module_name : str = None,
                                  mcp_module_filepath : str = None,
                                  custom_modules : list = None,
                                  import_mappings : str = None,
                                  check_vulnerabilities : bool = None,
                                  check_dependencies_compatibility : bool = None,
                                  check_full_dependencies_compatibility : bool = None,
                                  check_dependencies_licenses : bool = None):

        """
        Extract and add requirements from the MCP module.
        """

        if mcp_module_filepath is None:
            mcp_module_filepath = self.mcp_module_filepath

        if module_name is None:
            module_name = self.module_name

        if custom_modules is None:
            custom_modules = []

        if (mcp_module_filepath is not None) and \
            os.path.exists(mcp_module_filepath) \
                and os.path.isfile(mcp_module_filepath):

            self._add_requirements(
                module_filepath = mcp_module_filepath,
                custom_modules = custom_modules + [module_name],
                import_mappings = import_mappings,
                check_vulnerabilities = check_vulnerabilities,
                check_dependencies_compatibility = check_dependencies_compatibility,
                check_full_dependencies_compatibility = check_full_dependencies_compatibility,
                check_dependencies_licenses = check_dependencies_licenses,
                add_header = False
            )

    def add_readme(self,
                    example_notebook_path : str = None,
                    output_path : str = None,
                    execute_notebook : bool = None,
                    clean_package_docs : bool = True):

        """
        Make README file based on usage example.
        """


        if self.long_doc_h is None:
            self._initialize_long_doc_h(params={
                "module_name": self.module_name,
                "notebook_path": self.example_notebook_path,
                "kernel_name": self.kernel_name,
                "logger": self.logger
            })
        if example_notebook_path is None:
            example_notebook_path = self.example_notebook_path

        if clean_package_docs:
            self.clear_package_docs()

        output_path_docs = None
        if output_path is None:
            output_path = os.path.join(self.setup_directory,
                                       "README.md")

            if self.docs_path:
                output_path_docs = os.path.join(self.docs_path,
                                        f"{self.module_name}.md")

        self.logger.info(f"Adding README from {example_notebook_path} to {output_path}")

        if execute_notebook is None:
            execute_notebook = self.execute_readme_notebook

        if execute_notebook:
            # converting example notebook to md
            self.long_doc_h.convert_and_execute_notebook_to_md(
                notebook_path = example_notebook_path,
                output_path = output_path
            )
        else:
            self.long_doc_h.convert_notebook_to_md(
                notebook_path = example_notebook_path,
                output_path = output_path
            )

        if output_path_docs:
            shutil.copy(output_path, output_path_docs)
            additional_docs = [ad for ad in os.listdir(self.setup_directory) if ad.endswith(".png")]
            for ad in additional_docs:
                shutil.copy(os.path.join(self.setup_directory,
                                       ad), os.path.join(self.docs_path,
                                        ad))

    def add_extra_docs(self,
                       extra_docs_dir : str = None):

        """
        Add extra docs from provided path for a given package.
        """

        if self.long_doc_h is None:
            self._initialize_long_doc_h(params={
                "module_name": self.module_name,
                "notebook_path": self.example_notebook_path,
                "kernel_name": self.kernel_name,
                "logger": self.logger
            })
        if extra_docs_dir is None:
            extra_docs_dir = self.extra_docs_dir

        if extra_docs_dir:
            self.long_doc_h.prep_extra_docs(
                package_name = self.module_name,
                extra_docs_dir = extra_docs_dir,
                docs_path = self.docs_path)

    def clear_package_docs(self):

        """
        Remove docs in docs_path that were generated for this package.
        """

        if self.long_doc_h is None:
            self._initialize_long_doc_h(params={
                "module_name": self.module_name,
                "notebook_path": self.example_notebook_path,
                "kernel_name": self.kernel_name,
                "logger": self.logger
            })
        self.long_doc_h.clear_package_docs(
            package_name=self.module_name,
            docs_path=self.docs_path
        )




    def make_mkdocs_site(self):

        """
        Use provided docs to generate simple mkdocs site.
        """

        if self.add_mkdocs_site:

            if self.mkdocs_h is None:

                package_name = self.module_name

                module_content = LongDocHandler().read_module_content(
                    filepath=self.module_filepath)
                docstring = LongDocHandler().extract_module_docstring(
                    module_content=module_content)
                pypi_link = LongDocHandler().get_pypi_badge(
                    module_name=package_name)

                if (self.docs_path is not None) \
                    and (os.path.exists(self.docs_path)):
                    doc_files = os.listdir(self.docs_path)
                else:
                    doc_files = []

                docs_file_paths = {}

                package_docs = [doc_file for doc_file in doc_files \
                    if doc_file.startswith(package_name)]

                additional_images = []

                for package_doc in package_docs:

                    if package_doc == f"{package_name}.md":
                        package_doc_path = os.path.join(self.docs_path, package_doc)
                        if os.path.getsize(package_doc_path) > 0:
                            docs_file_paths[package_doc_path] = "description.md"
                    else:
                        docs_file_paths[os.path.join(self.docs_path,package_doc)] = package_doc

                    if os.path.isdir(os.path.join(self.docs_path,package_doc)):

                        package_docs = os.listdir(os.path.join(self.docs_path,package_doc))

                        for package_doc_f in package_docs:

                            if package_doc_f.endswith(".md"):
                                additional_images += LongDocHandler().get_referenced_images(
                                    md_file_path = os.path.join(self.docs_path,
                                        package_doc, package_doc_f)
                                )
                    else:

                        if package_doc.endswith(".md"):
                            additional_images += LongDocHandler().get_referenced_images(
                                md_file_path = os.path.join(self.docs_path,
                                    package_doc)
                            )

                # remove docs path from images path
                #additional_images = [os.path.relpath(p, self.docs_path) for p in additional_images]

                image_path_replacements = {}
                for img in additional_images:
                    docs_file_paths[os.path.join(self.docs_path,img)] = os.path.join(
                        "images",
                        os.path.basename(img))
                    image_path_replacements[
                        img] = os.path.join(
                        "images",
                        os.path.basename(img))

                if self.docs_file_paths:
                    docs_file_paths.update(self.docs_file_paths)

                if (self.release_notes_filepath is not None) \
                    and os.path.exists(self.release_notes_filepath):
                    docs_file_paths[self.release_notes_filepath] = "release-notes.md"

                # if (self.cli_docs_filepath is not None) \
                #     and os.path.exists(self.cli_docs_filepath):
                #     docs_file_paths[self.cli_docs_filepath] = "cli.md"


                self.mkdocs_h = self.mkdocs_class(
                    project_name = f"{package_name}_temp_mkdocs",
                    package_name = package_name,
                    docs_file_paths = docs_file_paths,
                    module_docstring = docstring,
                    pypi_badge = pypi_link,
                    license_badge=self.license_badge,
                    source_repo_url=self.source_repo_url,
                    source_repo_name=self.source_repo_name)

            self.mkdocs_h.create_mkdocs_dir()
            self.mkdocs_h.move_files_to_docs(
                image_path_replacements = image_path_replacements
            )
            self.mkdocs_h.generate_markdown_for_images()
            self.mkdocs_h.create_index()
            self.mkdocs_h.create_mkdocs_yml()
            self.mkdocs_h.build_mkdocs_site()

            if self.artifacts_filepaths is None:
                self.artifacts_filepaths = {}

            self.artifacts_filepaths['mkdocs'] = f"{package_name}_temp_mkdocs"

    def prepare_artifacts(self, artifacts_filepaths : dict = None):

        """
        Add artifacts to setup directory and its manifest.
        """

        if self.artifacts_h is None:
            self._initialize_artifacts_h(params={
                "module_name": self.module_name,
                "setup_directory": self.setup_directory,
                "artifacts_dir": self.artifacts_dir,
                "logger": self.logger
            })
        if artifacts_filepaths is None:
            artifacts_filepaths = self.artifacts_filepaths

        if artifacts_filepaths is None:
            artifacts_filepaths = {}

        if self.drawio_h is None:
            self._initialize_drawio_h(params={
                "drawio_filepath": self.drawio_filepath,
                "setup_directory": self.setup_directory,
                "logger": self.logger
            })
        self.drawio_h.prepare_drawio()

        additional_artifacts_filepaths = self.artifacts_h.load_additional_artifacts()

        artifacts_filepaths.update(additional_artifacts_filepaths)

        artifacts_filepaths_m = {name : import_path \
            for name, import_path in artifacts_filepaths.items() if name == 'mkdocs'}

        artifacts_filepaths_m.update({os.path.join('artifacts', name) : import_path \
            for name, import_path in artifacts_filepaths.items() if name != 'mkdocs'})

        artifacts_filepaths = artifacts_filepaths_m

        if self.add_artifacts:

            if (self.log_filepath is not None \
                and os.path.exists(self.log_filepath)):
                artifacts_filepaths['.paa.tracking/version_logs.csv'] = self.log_filepath

            if (self.release_notes_filepath is not None \
                and os.path.exists(self.release_notes_filepath)):
                artifacts_filepaths['.paa.tracking/release_notes.md'] = self.release_notes_filepath

            if (self.versions_filepath is not None \
                and os.path.exists(self.versions_filepath)):
                artifacts_filepaths['.paa.tracking/lsts_package_versions.yml'] = self.versions_filepath

            if (self.example_notebook_path is not None \
                and os.path.exists(self.example_notebook_path)):
                artifacts_filepaths['.paa.tracking/notebook.ipynb'] = self.example_notebook_path

            if (self.mapping_filepath is not None \
                and os.path.exists(self.mapping_filepath)):
                artifacts_filepaths['.paa.tracking/package_mapping.json'] = self.mapping_filepath

            if (self.licenses_filepath is not None \
                and os.path.exists(self.licenses_filepath)):
                artifacts_filepaths['.paa.tracking/package_licenses.json'] = self.licenses_filepath

            if (self.drawio_filepath is not None\
                and os.path.exists(self.drawio_filepath)):
                artifacts_filepaths['.paa.tracking/.drawio'] = self.drawio_filepath

            if (self.extra_docs_dir is not None\
                and os.path.exists(self.extra_docs_dir)):
                artifacts_filepaths['.paa.tracking/extra_docs'] = self.extra_docs_dir

            skills_dir = os.path.join("skills", self.module_name)
            if os.path.exists(skills_dir):
                artifacts_filepaths['.paa.tracking/skills'] = f"skills/{self.module_name}"

            if (self.tests_dir is not None\
                and os.path.exists(self.tests_dir)):
                artifacts_filepaths['tests'] = self.tests_dir

            if (self.config_filepath is not None \
                and os.path.exists(self.config_filepath)):
                artifacts_filepaths['.paa.tracking/.paa.config'] = self.config_filepath

            if (self.license_path is not None \
                and os.path.exists(self.license_path)):
                artifacts_filepaths['.paa.tracking/LICENSE'] = self.license_path

            if (self.notice_path is not None \
                and os.path.exists(self.notice_path)):
                artifacts_filepaths['.paa.tracking/NOTICE'] = self.notice_path

            pyproject_filepath = os.path.join(self.pyproject_dir, f"{self.module_name}.toml")
            if os.path.exists(pyproject_filepath):
                artifacts_filepaths['.paa.tracking/pyproject.toml'] = pyproject_filepath

            history_git_dir = os.path.join(".paa", "history", self.module_name, "git")
            if os.path.exists(history_git_dir) and '.paa.tracking/git' not in artifacts_filepaths:
                artifacts_filepaths['.paa.tracking/git'] = history_git_dir
            history_git_metadata_dir = os.path.join(history_git_dir, ".git")
            if os.path.exists(history_git_metadata_dir) and '.paa.tracking/git_repo' not in artifacts_filepaths:
                artifacts_filepaths['.paa.tracking/git_repo'] = history_git_metadata_dir

            if (self.module_filepath  is not None \
                and os.path.exists(self.module_filepath)):
                artifacts_filepaths[
                    f'.paa.tracking/python_modules/{self.module_name}.py'] = self.original_module_filepath

            if (self.local_dependacies_list  \
                and os.path.exists(self.dependencies_dir)):
                for component in self.local_dependacies_list:
                    artifacts_filepaths[
                    f'.paa.tracking/python_modules/components/{component}'] = os.path.join(
                        self.dependencies_dir, f"{component}")

            if 'artifact_urls' in self.metadata.keys():
                artifact_urls=self.metadata['artifact_urls']
                del self.metadata['artifact_urls']

                for artifact_name, artifact_url in artifact_urls.items():
                    artifacts_filepaths[
                        os.path.join('artifacts',artifact_name + '.link')] = artifact_url



        self.artifacts_h.make_manifest(
            artifacts_filepaths = artifacts_filepaths
        )

        self.artifacts_filepaths = self.artifacts_h.artifacts_filepaths

    def prep_setup_file(self,
                       module_name : str = None,
                       cli_module_filepath : str = None,
                       fastapi_routes_filepath : str = None,
                       streamlit_filepath : str = None,
                       mcp_module_filepath : str = None,
                       metadata : dict = None,
                       cli_metadata : dict = None,
                       requirements : list = None,
                       optional_requirements : list = None,
                       classifiers : list = None,
                       module_filepath : str = None,
                       module_docstring : str = None,
                       add_artifacts : bool = None,
                       artifacts_filepaths : dict = None):

        """
        Assemble setup.py file.
        """


        if self.setup_dir_h is None:
            self._initialize_setup_dir_h(params={
                "module_name": self.module_name,
                "module_filepath": self.module_filepath,
                "setup_directory": self.setup_directory,
                "pyproject_directory": self.pyproject_dir,
                "license_path": self.license_path,
                "license_label": self.license_label,
                "docs_url": self.docs_url,
                "version": self.metadata.get("version"),
                "logger": self.logger
            })
        if cli_module_filepath is None:
            cli_module_filepath = self.cli_module_filepath

        if fastapi_routes_filepath is None:
            fastapi_routes_filepath = self.fastapi_routes_filepath

        if streamlit_filepath is None:
            streamlit_filepath = self.streamlit_filepath
        if mcp_module_filepath is None:
            mcp_module_filepath = self.mcp_module_filepath

        if metadata is None:
            metadata = self.metadata

        if cli_metadata is None:
            cli_metadata = self.cli_metadata

        if requirements is None:
            requirements = self.requirements_list

        if optional_requirements is None:
            optional_requirements = self.optional_requirements_list

        if classifiers is None:
            classifiers = self.classifiers

        if module_filepath is None:
            module_filepath = self.module_filepath

        if module_name is None:
            module_name = self.module_name

        if add_artifacts is None:
            add_artifacts = self.add_artifacts

        if artifacts_filepaths is None:
            artifacts_filepaths = self.artifacts_filepaths

        if module_docstring is None:

            if self.long_doc_h is None:
                self._initialize_long_doc_h(params={
                    "module_name": self.module_name,
                    "notebook_path": self.example_notebook_path,
                    "kernel_name": self.kernel_name,
                    "logger": self.logger
                })
            module_content = self.long_doc_h.read_module_content(filepath = module_filepath)

            module_docstring = self.long_doc_h.extract_module_docstring(module_content = module_content)


        if cli_module_filepath is not None \
            and os.path.exists(cli_module_filepath) \
                and os.path.isfile(cli_module_filepath):

            if self.cli_h is None:
                self._initialize_cli_h(params={
                    "cli_module_filepath": self.cli_module_filepath,
                    "setup_directory": self.setup_directory,
                    "logger": self.logger
                })
            add_cli_tool = self.cli_h.prepare_script(
                cli_module_filepath = cli_module_filepath
            )
        else:
            add_cli_tool = None

        if fastapi_routes_filepath is not None \
            and os.path.exists(fastapi_routes_filepath) \
                and os.path.isfile(fastapi_routes_filepath):

            if self.fastapi_h is None:
                self._initialize_fastapi_h(params={
                    "fastapi_routes_filepath": self.fastapi_routes_filepath,
                    "setup_directory": self.setup_directory,
                    "logger": self.logger
                })
            add_fastapi = self.fastapi_h.prepare_routes(
                fastapi_routes_filepath = fastapi_routes_filepath
            )

        if streamlit_filepath is not None \
            and os.path.exists(streamlit_filepath) \
                and os.path.isfile(streamlit_filepath):

            if self.streamlit_h is None:
                self._initialize_streamlit_h(params={
                    "package_name": self.module_name,
                    "streamlit_filepath": self.streamlit_filepath,
                    "setup_directory": self.setup_directory,
                    "logger": self.logger
                })
            add_streamlit = self.streamlit_h.prepare_streamlit(
                streamlit_filepath = streamlit_filepath
            )

        if mcp_module_filepath is not None \
            and os.path.exists(mcp_module_filepath) \
                and os.path.isfile(mcp_module_filepath):

            if self.mcp_h is None:
                self._initialize_mcp_h(params={
                    "mcp_filepath": self.mcp_module_filepath,
                    "setup_directory": self.setup_directory,
                    "logger": self.logger
                })
            add_mcp = self.mcp_h.prepare_mcp(
                mcp_filepath = mcp_module_filepath
            )


        self.logger.info(f"Preparing setup file for {module_name.replace('_','-')} package ...")

        # create setup.py
        metadata_for_files = copy.deepcopy(metadata)
        cli_metadata_for_files = copy.deepcopy(cli_metadata)

        self.setup_dir_h.write_setup_file(module_name = module_name,
                                          module_docstring = module_docstring,
                                          metadata = copy.deepcopy(metadata_for_files),
                                          cli_metadata = copy.deepcopy(cli_metadata_for_files),
                                          requirements = requirements,
                                          optional_requirements = optional_requirements,
                                          classifiers = classifiers,
                                          add_cli_tool = add_cli_tool,
                                          add_artifacts = add_artifacts,
                                          artifacts_filepaths = artifacts_filepaths)

        self.setup_dir_h.write_pyproject_file(
            module_name=module_name,
            metadata=metadata_for_files,
            cli_metadata=cli_metadata_for_files,
            requirements=requirements,
            optional_requirements=optional_requirements,
            classifiers=classifiers,
            add_cli_tool=add_cli_tool
        )

        if self.artifacts_h is not None:
            self.artifacts_h.write_mafifest()


    def make_package(self,
                     setup_directory : str = None):

        """
        Create a package.
        """

        if setup_directory is None:
            setup_directory = self.setup_directory

        self.logger.info(f"Making package from {setup_directory} ...")

        # Define the command as a list of arguments
        command = ["python", os.path.join(setup_directory, "setup.py"), "sdist", "bdist_wheel"]

        # Execute the command
        result = subprocess.run(command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True)

        return result

    def test_install_package(self,
                             module_name : str = None,
                             remove_temp_files : bool = None,
                             skip_deps_install : bool = None):

        """
        Test install package to environment and optional remove temp files.
        """

        if module_name is None:
            module_name = self.module_name

        if remove_temp_files is None:
            remove_temp_files = self.remove_temp_files

        if skip_deps_install is None:
            skip_deps_install = self.skip_deps_install

        self.logger.info(f"Test installing {module_name} package ...")

        # Reinstall only wheel files matching the requested module.
        # This prevents cross-package installs when dist/ contains leftovers.
        module_name_candidates = {
            module_name,
            module_name.replace("_", "-"),
            module_name.replace("-", "_")
        }
        wheel_files = []
        available_wheels = []
        for filename in os.listdir('dist'):
            if not filename.endswith('-py3-none-any.whl'):
                continue
            available_wheels.append(filename)
            if any(filename.startswith(f"{candidate}-") for candidate in module_name_candidates):
                wheel_files.append(filename)

        if not wheel_files:
            raise FileNotFoundError(
                f"No wheel file for module '{module_name}' was found in dist/. "
                f"Available wheels: {available_wheels}"
            )

        for wheel_file in wheel_files:
            list_of_cmds = [sys.executable,
                            "-m", "pip", "install", "--force-reinstall"]

            if skip_deps_install:
                list_of_cmds.append("--no-deps")

            # Use POSIX-style wheel path for stable cross-platform command args.
            list_of_cmds.append(f"dist/{wheel_file}")

            subprocess.run(list_of_cmds, check=True)

        if remove_temp_files:
            # Clean up the build directories and other generated files
            shutil.rmtree('build', ignore_errors=True)
            shutil.rmtree('dist', ignore_errors=True)
            shutil.rmtree(module_name, ignore_errors=True)
            shutil.rmtree(f"{module_name}.egg-info", ignore_errors=True)

            if os.path.exists(f"{module_name}_temp_mkdocs"):
                shutil.rmtree(f"{module_name}_temp_mkdocs", ignore_errors=True)
