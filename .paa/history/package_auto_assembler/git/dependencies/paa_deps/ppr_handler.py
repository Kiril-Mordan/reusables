import logging
import os
import sys
import subprocess
import importlib
import importlib.metadata
import importlib.resources as pkg_resources
import csv
import shutil
import json
import re
import yaml
import pandas as pd
from pathlib import Path
import attrs #>=22.2.0
import attrsx

PAA_PATH_DEFAULTS = {
    "module_dir": "python_modules",
    "example_notebooks_path": "example_notebooks",
    "dependencies_dir": "python_modules/components",
    "licenses_dir": "licenses",
    "cli_dir": "cli",
    "mcp_dir": "mcp",
    "api_routes_dir": "api_routes",
    "streamlit_dir": "streamlit",
    "artifacts_dir": "artifacts",
    "drawio_dir": "drawio",
    "extra_docs_dir": "extra_docs",
    "tests_dir": "tests",
}

@attrsx.define
class PprHandler:

    """
    Prepares and handles python packaging repo with package-auto-assembler.
    """

    # inputs
    paa_dir = attrs.field(default=".paa")
    paa_config_file = attrs.field(default=".paa.config")
    paa_config = attrs.field(default=None)

    init_dirs = attrs.field(default=["module_dir", "example_notebooks_path",
            "dependencies_dir", "cli_dir", "mcp_dir", "api_routes_dir", "streamlit_dir",
            "artifacts_dir", "drawio_dir", "extra_docs_dir", "tests_dir"])

    module_dir = attrs.field(default=None)
    drawio_dir = attrs.field(default=None)
    docs_dir = attrs.field(default=None)

    pylint_threshold = attrs.field(default=None)

    # processed
    logger = attrs.field(default=None)
    logger_name = attrs.field(default='PPR Handler')
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

    def _create_init_paa_dir(self, paa_dir : str):

        os.makedirs(paa_dir)

        with open(os.path.join(paa_dir, 'package_licenses.json'),
        'w', encoding = 'utf-8') as init_file:
            init_file.write("{}")

        with open(os.path.join(paa_dir, 'package_mapping.json'),
        'w', encoding = 'utf-8') as init_file:
            init_file.write("{}")

    def _create_empty_tracking_files(self, paa_dir : str):

        os.makedirs(os.path.join(paa_dir,'tracking'))

        with open(os.path.join(paa_dir,'tracking',
        'lsts_package_versions.yml'),
            'w', encoding = "utf-8") as file:
            file.write("")

        log_file = open(os.path.join(paa_dir,'tracking','version_logs.csv'),
        'a',
        newline='',
        encoding="utf-8")
        csv_writer = csv.writer(log_file)
        csv_writer.writerow(['Timestamp', 'Package', 'Version'])

    def _create_init_requirements(self, paa_dir : str):

        os.makedirs(os.path.join(paa_dir,'requirements'))

        init_requirements = [
            ### dev requirements for tools
            'python-dotenv==1.0.0',
            'stdlib-list==0.10.0',
            'pytest==7.4.3',
            'pylint==3.0.3',
            'mkdocs-material==9.5.30',
            'jupyter',
            'ipykernel',
            'tox',
            'tox-gh-actions',
            'package-auto-assembler',
            'setuptools',
            'wheel', 
            'twine'
        ]

        with open(os.path.join(paa_dir, 'requirements_dev.txt'),
        'w', encoding = "utf-8") as file:
            for req in init_requirements:
                file.write(req + '\n')

    def _remove_trailing_whitespace_from_file(self, file_path : str):
        with open(file_path, 'r', encoding = "utf-8") as file:
            lines = file.readlines()

        # Remove trailing whitespace from each line
        cleaned_lines = [line.rstrip() + '\n' for line in lines]

        # Write the cleaned lines back to the file
        with open(file_path, 'w', encoding = "utf-8") as file:
            file.writelines(cleaned_lines)

        self.logger.debug(f"Cleaned {file_path}")

    def _remove_trailing_whitespace_from_directory(self, directory : str):
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self._remove_trailing_whitespace_from_file(file_path)

    def remove_trailing_whitespaces(self, file_dir_path : str):

        """
        Removes trailing whitespaces 
        from a given file or files in a directory.
        """

        if os.path.isfile(file_dir_path):
            # If it's a file, clean just that file
            if file_dir_path.endswith('.py'):
                self._remove_trailing_whitespace_from_file(file_dir_path)
            else:
                self.logger.error(f"{file_dir_path} is not a Python file.")
        elif os.path.isdir(file_dir_path):
            # If it's a directory, clean all .py files within it
            self._remove_trailing_whitespace_from_directory(file_dir_path)
        else:
            self.logger.error(f"{file_dir_path} is not a valid file or directory.")


    def run_pylint_tests(self, 
                         module_dir : str = None,
                         pylint_threshold : str = None,
                         files_to_check : list = None):

        """
        Run pylint tests for a given file, files or files in a directory.
        """

        if module_dir is None:
            module_dir = self.module_dir

        if pylint_threshold is None:
            pylint_threshold = self.pylint_threshold

        if pylint_threshold:
            pylint_threshold = str(pylint_threshold)

        paa_path = pkg_resources.files('package_auto_assembler')

        if not os.path.exists(paa_path):
            return 1

        script_path = os.path.join(paa_path,
                                   "artifacts",
                                   "tools",
                                   "pylint_test.sh")

        if not os.path.exists(script_path):
            return 2

        list_of_cmds = [script_path, 
                        "--module-directory",
                        module_dir]

        if pylint_threshold:
            list_of_cmds += ["--threshold", pylint_threshold]

        if files_to_check:
            list_of_cmds += files_to_check

        try:
            subprocess.run(list_of_cmds, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)


        return 0



    def convert_drawio_to_png(self,
                              module_name : str = None,
                              drawio_dir : str = None,
                              docs_dir : str = None):

        """
        Converts drawio files in ppr into png files for a package.
        """

        if drawio_dir is None:
            drawio_dir = self.drawio_dir

        if docs_dir is None:
            docs_dir = self.docs_dir

        # Remove previously generated drawio PNGs for affected package(s),
        # while preserving notebook-derived images (e.g., *_cell23_out0.png).
        self._cleanup_existing_drawio_pngs(
            module_name=module_name,
            drawio_dir=drawio_dir,
            docs_dir=docs_dir
        )

        paa_path = pkg_resources.files('package_auto_assembler')

        if not os.path.exists(paa_path):
            return 1

        script_path = os.path.join(paa_path,
                                   "artifacts",
                                   "tools",
                                   "convert_drawio_to_png.sh")

        if not os.path.exists(script_path):
            return 2

        list_of_cmds = [script_path, drawio_dir, docs_dir]

        if module_name:
            list_of_cmds.append(os.path.join(drawio_dir, f"{module_name}.drawio"))

        subprocess.run(list_of_cmds, check=True)

        return 0

    def _cleanup_existing_drawio_pngs(self,
                                      module_name : str = None,
                                      drawio_dir : str = None,
                                      docs_dir : str = None):

        """
        Remove previously generated drawio PNG files for selected package(s)
        before conversion, excluding notebook-derived PNG files.
        """

        if not docs_dir or not os.path.exists(docs_dir):
            return

        if not drawio_dir or not os.path.exists(drawio_dir):
            return

        if module_name:
            drawio_targets = [module_name]
        else:
            drawio_targets = [
                os.path.splitext(filename)[0]
                for filename in os.listdir(drawio_dir)
                if filename.endswith(".drawio")
            ]

        if not drawio_targets:
            return

        notebook_png_pattern = re.compile(r".*_cell\d+_out\d+\.png$")
        removed_count = 0

        for filename in os.listdir(docs_dir):
            if not filename.endswith(".png"):
                continue

            if notebook_png_pattern.match(filename):
                continue

            if any(filename.startswith(f"{target}-") for target in drawio_targets):
                filepath = os.path.join(docs_dir, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    removed_count += 1

        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} stale drawio png file(s) from {docs_dir}")

    def init_from_paa_config(self, default_config : dict):

        config = self.paa_config_file
        init_dirs = self.init_dirs

        if os.path.exists(config):
            with open(config, 'r', encoding = "utf-8") as file:
                paa_config = yaml.safe_load(file)
            paa_config = paa_config or {}

            effective_config = (default_config or {}).copy()
            for key, value in paa_config.items():
                if value is None:
                    continue
                if isinstance(value, str) and value.strip() == "":
                    continue
                effective_config[key] = value

            py_ignore = """# Ignore all files
*

# Allow only .py files
!*.py

# Allow all directories (so .py files in subdirectories are also tracked)
!*/         
            """

            ipynb_ignore = """# Ignore all files
*

# Allow only .ipynb files
!*.ipynb
       
            """

            drawio_ignore = """# Ignore all files
*

# Allow only .ipynb files
!*.drawio
       
            """

            gitignore_dict = {
                "module_dir" : py_ignore,
                "example_notebooks_path" : ipynb_ignore,
                "dependencies_dir" : py_ignore,
                "cli_dir" : py_ignore,
                "mcp_dir" : py_ignore,
                "api_routes_dir" : py_ignore,
                "streamlit_dir" : py_ignore,
                "drawio_dir" : drawio_ignore

            }

            for d in init_dirs:

                if effective_config.get(d):
                    if not os.path.exists(effective_config.get(d)):
                        os.makedirs(effective_config.get(d))
                    else:
                        self.logger.warning(f"{effective_config.get(d)} already exists!")

                    gitignore_path = os.path.join(effective_config.get(d), '.gitignore')

                    if gitignore_dict.get(d):
                        gitignore_text = gitignore_dict.get(d)
                    else:
                        gitignore_text = "__pycache__"

                    if not os.path.exists(gitignore_path):
                        with open(gitignore_path, "w", encoding = "utf-8") as file:
                            file.write(gitignore_text)
                    else:
                        self.logger.warning(f"{gitignore_path} already exists!")
            
        else:
            with open(config, 'w', encoding='utf-8') as file:
                yaml.safe_dump(default_config, file, sort_keys=False)

        


    def init_paa_dir(self, paa_dir : str = None):

        """
        Prepares .paa dir for packaging
        """

        if paa_dir is None:
            paa_dir = self.paa_dir

        try:

            if not os.path.exists(paa_dir):
                self._create_init_paa_dir(paa_dir = paa_dir)

            if not os.path.exists(os.path.join(paa_dir,'tracking')):
                self._create_empty_tracking_files(paa_dir = paa_dir)
            if not os.path.exists(os.path.join(paa_dir,'requirements')):
                self._create_init_requirements(paa_dir = paa_dir)
            if not os.path.exists(os.path.join(paa_dir,'requirements','.gitignore')):   

                rq_gitignore = """"""

                with open(os.path.join(paa_dir,'requirements','.gitignore'),
            'w', encoding = 'utf-8') as gitignore:
                    gitignore.write(rq_gitignore)
            if not os.path.exists(os.path.join(paa_dir,'release_notes')):
                os.makedirs(os.path.join(paa_dir,'release_notes'))
            if not os.path.exists(os.path.join(paa_dir,'release_notes','.gitignore')):   

                rn_gitignore = """# Ignore everything by default
*

# Allow markdown files
!*.md            
                """

                with open(os.path.join(paa_dir,'release_notes','.gitignore'),
            'w', encoding = 'utf-8') as gitignore:
                    gitignore.write(rn_gitignore)
            if not os.path.exists(os.path.join(paa_dir,'docs')):
                os.makedirs(os.path.join(paa_dir,'docs'))
            if not os.path.exists(os.path.join(paa_dir,'docs','.gitignore')):   

                docs_gitignore = """# Ignore everything by default
*

# Allow markdown files
!*.md

# Allow PNG image files
!*.png

# Allow traversal into subdirectories
!**/              
                """

                with open(os.path.join(paa_dir,'docs','.gitignore'),
            'w', encoding = 'utf-8') as gitignore:
                    gitignore.write(docs_gitignore)

        except Exception as e:
            self.logger.warning("Failed to initialize paa dir!")
            self.logger.error(e)
            return False

        return True

    def init_ppr_repo(self, workflows_platform : str = None):

        """
        Prepares ppr for package-auto-assembler.
        """

        if workflows_platform:

            if not os.path.exists(".paa"):
                self.init_paa_dir()
            else:
                self.logger.warning(f".paa already exists!")

            paa_path = pkg_resources.files('package_auto_assembler')

            if not os.path.exists(paa_path):
                return False

            template_path = os.path.join(paa_path,
                                    "artifacts",
                                    "ppr_workflows",
                                    workflows_platform)

            if workflows_platform == 'github':
                other_files = ['tox_github.ini', '.pylintrc']
            else:
                other_files = ['tox_azure.ini', '.pylintrc']

            if not os.path.exists(template_path):

                return False

            README_path = os.path.join(paa_path,
                                    "artifacts",
                                    "ppr_workflows",
                                    workflows_platform,
                                    "docs",
                                    "README_base.md"
                                    )

            if workflows_platform == 'github':
                workflows_platform = '.github'

            if workflows_platform == 'azure':
                workflows_platform = '.azure'

            if not os.path.exists(workflows_platform):
                shutil.copytree(template_path, workflows_platform)
            else:
                self.logger.warning(f"{workflows_platform} already exists!")

            for f in other_files:

                artifact_path = os.path.join(paa_path,
                                    "artifacts",
                                    "ppr_workflows",
                                    f)

                if f == "tox_github.ini":
                    f = "tox.ini"

                if f == "tox_azure.ini":
                    f = "tox.ini"

                if os.path.exists(artifact_path):
                    if not os.path.exists(f):
                        shutil.copy(artifact_path, f)

        
            if os.path.exists(README_path):
                if not os.path.exists("README.md"):
                    shutil.copy(README_path, "README.md")

            return True

        return False

    def _copy_missing_files(self, src : str, dst : str):
        """
        Copy only missing files and directories from src to dst.

        Args:
            src (str): Source directory.
            dst (str): Destination directory.
        """
        if not os.path.exists(dst):
            os.makedirs(dst)

        for root, dirs, files in os.walk(src):
            # Construct the relative path from the source root
            rel_path = os.path.relpath(root, src)
            dest_root = os.path.join(dst, rel_path)

            # Create directories in the destination if they don't exist
            for directory in dirs:
                dest_dir = os.path.join(dest_root, directory)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                else:
                    self.logger.warning(f"{dest_dir} already exists!")

            # Copy files that don't exist in the destination
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_root, file)

                if not os.path.exists(dest_file):
                    shutil.copy2(src_file, dest_file)  # Preserve metadata
                else:
                    self.logger.warning(f"{dest_file} already exists!")

    def _unfold_paa_config(self, paa_tracking_dir):

        self.logger.debug("Preparing .paa.config ...")

        package_paa_config_path = os.path.join(paa_tracking_dir, ".paa.config")
        repo_paa_config_path = ".paa.config"

        with open(package_paa_config_path, 'r', encoding = "utf-8") as file:
            paa_config = yaml.safe_load(file) or {}

        if os.path.exists(repo_paa_config_path):
            with open(repo_paa_config_path, 'r', encoding = "utf-8") as file:
                repo_paa_config = yaml.safe_load(file)

            for key, value in (repo_paa_config or {}).items():
                if value is None:
                    continue
                if isinstance(value, str) and value.strip() == "":
                    continue
                paa_config[key] = value
        else:
            shutil.copy(package_paa_config_path, repo_paa_config_path)

        for key, default_value in PAA_PATH_DEFAULTS.items():
            value = paa_config.get(key)
            if value is None:
                paa_config[key] = default_value
            elif isinstance(value, str) and value.strip() == "":
                paa_config[key] = default_value

        return paa_config

    def _unfold_components(self, 
                         paa_tracking_dir : str, 
                         paa_config : dict):

        if paa_config.get("dependencies_dir"):

            self.logger.debug(f"Preparing components ...")
            p_components_path = os.path.join(paa_tracking_dir,
                "python_modules", "components") 

            r_components_path = paa_config.get("dependencies_dir")

            if not os.path.exists(r_components_path):
                os.makedirs(r_components_path)

            if os.path.exists(p_components_path):
                self._copy_missing_files(p_components_path,
                                r_components_path)

                            
    def _unfold_dirs(self,
                     repo_dir : str,
                     dir_type : str,
                     packaged_name : str,
                    package_path : str,
                    module_name_subdir : bool,
                    module_name : str):

        if repo_dir:

            self.logger.debug(f"Preparing {dir_type} ...")
            p_dir_path = os.path.join(package_path, 
                                        packaged_name) 

            if not os.path.exists(repo_dir):
                os.makedirs(repo_dir)

            if module_name_subdir:
                repo_path = os.path.join(repo_dir, module_name)
            else:
                repo_path = repo_dir

            if os.path.exists(p_dir_path):
                if module_name_subdir:
                    # These directories are package-owned; replace to make unfold idempotent.
                    if os.path.exists(repo_path):
                        shutil.rmtree(repo_path)
                    shutil.copytree(p_dir_path, repo_path)
                else:
                    # Shared directories (e.g. components) should merge without deleting others.
                    self._copy_missing_files(p_dir_path, repo_path)


    def _unfold_file(self,
                    repo_path : str,
                    file_type : str,
                    file_extension : str,
                    packaged_name : str,
                    package_path : str,
                    module_name : str,
                    target_name : str = None):

        if repo_path:

            self.logger.debug(f"Preparing {file_type} ...")

            p_module_path = os.path.join(package_path, packaged_name)
            if target_name is None:
                target_name = f"{module_name}{file_extension}"

            r_module_path = os.path.join(repo_path, target_name)

            if not os.path.exists(repo_path):
                os.makedirs(repo_path)

            if os.path.exists(p_module_path):
                shutil.copy(p_module_path, r_module_path)
            elif os.path.exists(r_module_path):
                self.logger.warning(f"{p_module_path} was not found, keeping existing {r_module_path}.")

    def _remove_unfolded_components(self,
                                    module_name : str,
                                    repo_dir : str,
                                    module_dir : str = None):

        """
        Remove only component files that are tracked inside the installed package.
        """

        if not repo_dir:
            return

        try:
            package_path = pkg_resources.files(module_name)
            tracked_components_path = os.path.join(
                package_path, ".paa.tracking", "python_modules", "components")
        except Exception as e:
            self.logger.warning(f"Could not inspect tracked components for {module_name}: {e}")
            return

        if not os.path.exists(tracked_components_path):
            return

        # Keep components that are still referenced by other top-level modules.
        # This uses repository-local source usage to avoid removing shared deps.
        in_use_component_names = set()
        if module_dir and os.path.exists(module_dir):
            for filename in os.listdir(module_dir):
                if not filename.endswith(".py"):
                    continue
                if filename == f"{module_name}.py":
                    continue
                module_file = os.path.join(module_dir, filename)
                if not os.path.isfile(module_file):
                    continue
                try:
                    with open(module_file, "r", encoding="utf-8") as file:
                        module_content = file.read()
                except Exception:
                    continue
                for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", module_content):
                    in_use_component_names.add(token)

        for root, dirs, files in os.walk(tracked_components_path):
            rel_root = os.path.relpath(root, tracked_components_path)
            repo_root = os.path.join(repo_dir, rel_root) if rel_root != "." else repo_dir

            for file_name in files:
                component_name = Path(file_name).stem
                if component_name in in_use_component_names:
                    continue
                repo_file = os.path.join(repo_root, file_name)
                if os.path.exists(repo_file):
                    os.remove(repo_file)

            for dir_name in dirs:
                repo_subdir = os.path.join(repo_root, dir_name)
                if os.path.exists(repo_subdir) and not os.listdir(repo_subdir):
                    os.rmdir(repo_subdir)

    def _unfold_lsts_package_version(self, 
                                     paa_tracking_dir : str,
                                     module_name : str):

        self.logger.debug(f"Preparing lsts package version ...")

        p_versions_filepath = os.path.join(
            paa_tracking_dir, "lsts_package_versions.yml")
        r_versions_filepath = ".paa/tracking/lsts_package_versions.yml"
        os.makedirs(os.path.dirname(r_versions_filepath), exist_ok=True)

        if os.path.exists(p_versions_filepath):
            with open(p_versions_filepath, 'r', encoding = "utf-8") as file:
                # Load the contents of the file
                p_lsts_versions = yaml.safe_load(file) or {}
        else:
            p_lsts_versions = {}

        if os.path.exists(r_versions_filepath):
            with open(r_versions_filepath, 'r', encoding = "utf-8") as file:
                # Load the contents of the file
                r_lsts_versions = yaml.safe_load(file) or {}
        else:
            r_lsts_versions = {}

        r_lsts_versions[module_name] = p_lsts_versions.get(module_name, "0.0.0")

        with open(r_versions_filepath, 'w', encoding='utf-8') as file:
            yaml.safe_dump(r_lsts_versions, file)

    def _unfold_version_logs(self, 
                            paa_tracking_dir : str,
                            module_name : str):

        self.logger.debug(f"Preparing version logs ...")

        try:

            p_versions_filepath = os.path.join(
                paa_tracking_dir, "version_logs.csv")
            r_versions_filepath = ".paa/tracking/version_logs.csv"
            os.makedirs(os.path.dirname(r_versions_filepath), exist_ok=True)

            if os.path.exists(p_versions_filepath):
                p_logs = pd.read_csv(p_versions_filepath)
            else:
                p_logs = pd.DataFrame([], columns=["Timestamp","Package","Version"])

            if os.path.exists(r_versions_filepath):
                r_logs = pd.read_csv(r_versions_filepath)
            else:
                r_logs = pd.DataFrame([], columns=["Timestamp","Package","Version"])

            new_logs = pd.concat([
                p_logs.query(f"Package == '{module_name}'"),
                r_logs.query(f"Package != '{module_name}'")]).sort_values(by="Timestamp", ascending=True)
        
            new_logs.to_csv(r_versions_filepath, index=False)
        
        except Exception as e:
            self.logger.error(f"Merging version logs for {module_name} failed! {e}")

    def _unfold_package_mappings(self, 
                            paa_tracking_dir : str,
                            module_name : str):

        self.logger.debug(f"Preparing package mappings ...")

        try:

            p_mappings_filepath = os.path.join(
                paa_tracking_dir, "package_mapping.json")
            r_mappings_filepath = ".paa/package_mapping.json"
            os.makedirs(os.path.dirname(r_mappings_filepath), exist_ok=True)

            if os.path.exists(p_mappings_filepath):
                with open(p_mappings_filepath, 'r',
                encoding = "utf-8") as file:
                    p_mappings = json.load(file)
            else:
                p_mappings = {}

            if os.path.exists(r_mappings_filepath):
                with open(r_mappings_filepath, 'r',
                encoding = "utf-8") as file:
                    r_mappings = json.load(file)
            else:
                r_mappings = {}

            r_mappings.update(p_mappings)
        
            with open(r_mappings_filepath, "w", encoding = "utf-8") as json_file:
                json.dump(r_mappings, json_file, indent=4)
        
        except Exception as e:
            self.logger.error(f"Merging package mappings for {module_name} failed! {e}")

    def _unfold_package_licenses(self, 
                            paa_tracking_dir : str,
                            module_name : str):

        self.logger.debug(f"Preparing package licenses ...")

        try:

            p_mappings_filepath = os.path.join(
                paa_tracking_dir, "package_licenses.json")
            r_mappings_filepath = ".paa/package_licenses.json"
            os.makedirs(os.path.dirname(r_mappings_filepath), exist_ok=True)

            if os.path.exists(p_mappings_filepath):
                with open(p_mappings_filepath, 'r',
                encoding = "utf-8") as file:
                    p_mappings = json.load(file)
            else:
                p_mappings = {}

            if os.path.exists(r_mappings_filepath):
                with open(r_mappings_filepath, 'r',
                encoding = "utf-8") as file:
                    r_mappings = json.load(file)
            else:
                r_mappings = {}

            r_mappings.update(p_mappings)
        
            with open(r_mappings_filepath, "w", encoding = "utf-8") as json_file:
                json.dump(r_mappings, json_file, indent=4)
        
        except Exception as e:
            self.logger.error(f"Merging package licenses for {module_name} failed! {e}")

    def _restore_checkpoint_git_metadata(self, module_name: str, paa_tracking_dir: str):
        module_history_dir = os.path.join(".paa", "history", module_name)
        work_tree_dir = os.path.join(module_history_dir, "git")
        packaged_repo_metadata_dir = os.path.join(paa_tracking_dir, "git_repo")
        dot_git_dir = os.path.join(work_tree_dir, ".git")

        if not os.path.exists(work_tree_dir):
            return

        if os.path.exists(dot_git_dir):
            return

        if os.path.exists(packaged_repo_metadata_dir):
            os.makedirs(work_tree_dir, exist_ok=True)
            shutil.copytree(packaged_repo_metadata_dir, dot_git_dir)

    def _unfold_checkpoint_history(self, module_name: str, paa_tracking_dir: str):
        module_history_dir = os.path.join(".paa", "history", module_name)
        packaged_history_dir = os.path.join(paa_tracking_dir, "git")
        target_history_dir = os.path.join(module_history_dir, "git")

        if not os.path.exists(packaged_history_dir):
            return

        os.makedirs(module_history_dir, exist_ok=True)

        if os.path.exists(target_history_dir):
            shutil.rmtree(target_history_dir)
        shutil.copytree(packaged_history_dir, target_history_dir)

        # Cleanup for older unfold behavior that placed history files
        # directly under .paa/history/<module_name> instead of /git.
        for entry in os.listdir(module_history_dir):
            if entry == "git":
                continue
            entry_path = os.path.join(module_history_dir, entry)
            if os.path.isdir(entry_path):
                shutil.rmtree(entry_path)
            else:
                os.remove(entry_path)

    def unfold_package(self, 
                       module_name : str = None):

        """
        Unfold package into PPR.
        """

        module_name = module_name.replace("-","_")

        package_path = pkg_resources.files(module_name)
        if not os.path.exists(package_path):
            return 1

        paa_tracking_dir = os.path.join(package_path, ".paa.tracking")

        if not os.path.exists(paa_tracking_dir):
            return 2

        paa_config = self._unfold_paa_config(paa_tracking_dir = paa_tracking_dir)

        files_to_unfold = {
            "main_module" : {
                "repo_path" : paa_config.get("module_dir"),
                "file_extension" : ".py",
                "packaged_name" : os.path.join(
                    ".paa.tracking", 
                    "python_modules",
                    f"{module_name}.py"),
            },
            "cli" : {
                "repo_path" : paa_config.get("cli_dir"),
                "file_extension" : ".py",
                "packaged_name" : f"cli.py",
            },
            "mcp" : {
                "repo_path" : paa_config.get("mcp_dir"),
                "file_extension" : ".py",
                "packaged_name" : f"mcp_server.py",
            },
            "routes" : {
                "repo_path" : paa_config.get("api_routes_dir"),
                "file_extension" : ".py",
                "packaged_name" : f"routes.py",
            },
            "streamlit" : {
                "repo_path" : paa_config.get("streamlit_dir"),
                "file_extension" : ".py",
                "packaged_name" : f"streamlit.py",
            },
            "example_notebooks" : {
                "repo_path" : paa_config.get("example_notebooks_path"),
                "file_extension" : ".ipynb",
                "packaged_name" : os.path.join(
                    ".paa.tracking", 
                    f"notebook.ipynb"),
            },
            "drawio" : {
                "repo_path" : paa_config.get("drawio_dir"),
                "file_extension" : ".drawio",
                "packaged_name" : os.path.join(
                    ".paa.tracking", 
                    f".drawio")
            },
            "release_notes" : {
                "repo_path" : ".paa/release_notes",
                "file_extension" : ".md",
                "packaged_name" : os.path.join(
                    ".paa.tracking", 
                    f"release_notes.md"),
            },
            "pyproject" : {
                "repo_path" : ".paa/pyproject",
                "file_extension" : ".toml",
                "packaged_name" : os.path.join(
                    ".paa.tracking",
                    "pyproject.toml"),
            },
            "license" : {
                "repo_path" : os.path.join(paa_config.get("licenses_dir", "licenses"), module_name),
                "file_extension" : "",
                "packaged_name" : os.path.join(
                    ".paa.tracking",
                    "LICENSE"),
                "target_name" : "LICENSE",
            },
            "notice" : {
                "repo_path" : os.path.join(paa_config.get("licenses_dir", "licenses"), module_name),
                "file_extension" : "",
                "packaged_name" : os.path.join(
                    ".paa.tracking",
                    "NOTICE"),
                "target_name" : "NOTICE",
            }
        }

        dirs_to_unfold = {
            "components" : {
                "repo_dir" : paa_config.get("dependencies_dir"),
                "module_name_subdir" : False,
                "packaged_name" : os.path.join(
                    ".paa.tracking", 
                    "python_modules",
                    f"components"),

            },
            "tests" : {
                "repo_dir" : paa_config.get("tests_dir"),
                "module_name_subdir" : True,
                "packaged_name" : "tests",

            },
            "artifacts" : {
                "repo_dir" : paa_config.get("artifacts_dir"),
                "module_name_subdir" : True,
                "packaged_name" : "artifacts",

            },
            "extra_docs" : {
                "repo_dir" : paa_config.get("extra_docs_dir"),
                "module_name_subdir" : True,
                "packaged_name" : os.path.join(
                    ".paa.tracking", "extra_docs"),

            },
            "skills" : {
                "repo_dir" : "skills",
                "module_name_subdir" : True,
                "packaged_name" : os.path.join(
                    ".paa.tracking", "skills"),

            }
        }

        # Ensure tracking skeleton exists even in partially initialized folders.
        self.init_paa_dir()

        for file_name, file_spec in files_to_unfold.items():

            self._unfold_file(
                **file_spec,
                package_path = package_path,
                module_name = module_name,
                file_type = file_name
            )

        for dir_name, dir_spec in dirs_to_unfold.items():

            self._unfold_dirs(
                **dir_spec,
                package_path = package_path,
                module_name = module_name,
                dir_type = dir_name
            )

        self._unfold_lsts_package_version(
            paa_tracking_dir = paa_tracking_dir,
            module_name = module_name
        )
        self._unfold_version_logs(
            paa_tracking_dir = paa_tracking_dir,
            module_name = module_name
        )
        self._unfold_package_mappings(
            paa_tracking_dir = paa_tracking_dir,
            module_name = module_name
        )
        self._unfold_package_licenses(
            paa_tracking_dir = paa_tracking_dir,
            module_name = module_name
        )
        self._unfold_checkpoint_history(
            module_name=module_name,
            paa_tracking_dir=paa_tracking_dir
        )
        self._restore_checkpoint_git_metadata(
            module_name=module_name,
            paa_tracking_dir=paa_tracking_dir
        )

    def _remove_dirs(self,
                     repo_dir : str,
                     dir_type : str,
                    module_name_subdir : bool,
                    module_name : str):

        if repo_dir:

            self.logger.debug(f"Removing {dir_type} for {module_name} ...")

            if module_name_subdir:
                repo_path = os.path.join(repo_dir, module_name)
            else:
                repo_path = repo_dir

            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)


    def _remove_file(self,
                    repo_path : str,
                    file_type : str,
                    file_extension : str,
                    module_name : str,
                    target_name : str = None):

        if repo_path:

            self.logger.debug(f"Removing {file_type} for {module_name} ...")

            if target_name is None:
                target_name = f"{module_name}{file_extension}"

            r_module_path = os.path.join(repo_path, target_name)

            if os.path.exists(r_module_path):
                os.remove(r_module_path)


    def _remove_lsts_package_version(self, 
                                     module_name : str):

        self.logger.debug(f"Cleaning lsts package version ...")

        r_versions_filepath = ".paa/tracking/lsts_package_versions.yml"

        if os.path.exists(r_versions_filepath):
            with open(r_versions_filepath, 'r', encoding = "utf-8") as file:
                # Load the contents of the file
                r_lsts_versions = yaml.safe_load(file) or {}
        else:
            r_lsts_versions = {}

        if r_lsts_versions.get(module_name):
            del r_lsts_versions[module_name]

            with open(r_versions_filepath, 'w', encoding='utf-8') as file:
                yaml.safe_dump(r_lsts_versions, file)

    def _remove_version_logs(self, 
                            module_name : str):

        self.logger.debug(f"Cleaning version logs ...")

        try:

            r_versions_filepath = ".paa/tracking/version_logs.csv"

            if os.path.exists(r_versions_filepath):
                r_logs = pd.read_csv(r_versions_filepath)
            else:
                r_logs = pd.DataFrame([], columns=["Timestamp","Package","Version"])

            new_logs = r_logs.query(f"Package != '{module_name}'")
        
            new_logs.to_csv(r_versions_filepath, index=False)
        
        except Exception as e:
            self.logger.error(f"Merging version logs for {module_name} failed! {e}")

    def remove_package(self, 
                       module_name : str = None):

        """
        Remove package from PPR.
        """

        module_name = module_name.replace("-","_")

        repo_paa_config_path = ".paa.config"

        paa_config = {}
        if self.paa_config:
            paa_config = self.paa_config

        if os.path.exists(repo_paa_config_path):
            with open(repo_paa_config_path, 'r', encoding = "utf-8") as file:
                repo_paa_config = yaml.safe_load(file) or {}

            paa_config.update(repo_paa_config)
        else:
            return 1

        for key, default_value in PAA_PATH_DEFAULTS.items():
            value = paa_config.get(key)
            if value is None:
                paa_config[key] = default_value
            elif isinstance(value, str) and value.strip() == "":
                paa_config[key] = default_value

        files_to_remove = {
            "main_module" : {
                "repo_path" : paa_config.get("module_dir"),
                "file_extension" : ".py"
            },
            "cli" : {
                "repo_path" : paa_config.get("cli_dir"),
                "file_extension" : ".py",
            },
            "mcp" : {
                "repo_path" : paa_config.get("mcp_dir"),
                "file_extension" : ".py",
            },
            "routes" : {
                "repo_path" : paa_config.get("api_routes_dir"),
                "file_extension" : ".py",
            },
            "streamlit" : {
                "repo_path" : paa_config.get("streamlit_dir"),
                "file_extension" : ".py",
            },
            "example_notebooks" : {
                "repo_path" : paa_config.get("example_notebooks_path"),
                "file_extension" : ".ipynb",
            },
            "drawio" : {
                "repo_path" : paa_config.get("drawio_dir"),
                "file_extension" : ".drawio"
            },
            "release_notes" : {
                "repo_path" : ".paa/release_notes",
                "file_extension" : ".md"
            },
            "pyproject" : {
                "repo_path" : ".paa/pyproject",
                "file_extension" : ".toml"
            },
            "license" : {
                "repo_path" : os.path.join(paa_config.get("licenses_dir", "licenses"), module_name),
                "file_extension" : "",
                "target_name" : "LICENSE",
            },
            "notice" : {
                "repo_path" : os.path.join(paa_config.get("licenses_dir", "licenses"), module_name),
                "file_extension" : "",
                "target_name" : "NOTICE",
            }
        }

        dirs_to_remove = {
            "tests" : {
                "repo_dir" : paa_config.get("tests_dir"),
                "module_name_subdir" : True

            },
            "artifacts" : {
                "repo_dir" : paa_config.get("artifacts_dir"),
                "module_name_subdir" : True,

            },
            "extra_docs" : {
                "repo_dir" : paa_config.get("extra_docs_dir"),
                "module_name_subdir" : True

            },
            "skills" : {
                "repo_dir" : "skills",
                "module_name_subdir" : True

            },
            "checkpoint_history" : {
                "repo_dir" : os.path.join(".paa", "history"),
                "module_name_subdir" : True
            }
        }

        if not os.path.exists(".paa"):
            self.init_paa_dir()

        for file_name, file_spec in files_to_remove.items():

            self._remove_file(
                **file_spec,
                module_name = module_name,
                file_type = file_name
            )

        licenses_package_dir = os.path.join(paa_config.get("licenses_dir", "licenses"), module_name)
        if os.path.exists(licenses_package_dir) and not os.listdir(licenses_package_dir):
            os.rmdir(licenses_package_dir)

        self._remove_unfolded_components(
            module_name=module_name,
            repo_dir=paa_config.get("dependencies_dir"),
            module_dir=paa_config.get("module_dir")
        )

        for dir_name, dir_spec in dirs_to_remove.items():

            self._remove_dirs(
                **dir_spec,
                module_name = module_name,
                dir_type = dir_name
            )

        self._remove_lsts_package_version(
            module_name = module_name
        )
        self._remove_version_logs(
            module_name = module_name
        )

    def _rename_dirs(self,
                     repo_dir : str,
                     dir_type : str,
                    module_name : str,
                    new_module_name : str):

        if repo_dir:

            self.logger.debug(f"Renaming {dir_type} for {module_name} ...")

            repo_path = os.path.join(repo_dir, module_name)
            new_repo_path = os.path.join(repo_dir, new_module_name)
                  
            if os.path.exists(repo_path) and (not os.path.exists(new_repo_path)):
                os.rename(repo_path, new_repo_path)


    def _rename_file(self,
                    repo_path : str,
                    file_type : str,
                    file_extension : str,
                    module_name : str,
                    new_module_name : str):

        if repo_path:

            self.logger.debug(f"Renaming {file_type} for {module_name} ...")

            r_module_path = os.path.join(
                repo_path,
                f"{module_name}{file_extension}"
            )

            r_new_module_path = os.path.join(
                repo_path,
                f"{new_module_name}{file_extension}"
            )

            if os.path.exists(r_module_path) and (not os.path.exists(r_new_module_path)):
                os.rename(r_module_path, r_new_module_path)

    def _replace_package_name(self, 
                              repo_path : str,
                              package_name : str, 
                              new_package_name : str):

        file_path = None
        if repo_path:
            file_path = os.path.join(repo_path, f"{new_package_name}.py")

        if file_path and os.path.exists(file_path):
            
            with open(file_path, 'r', encoding = 'utf-8') as file:
                content = file.readlines()

            modified = False
            new_content = []

            for line in content:
                if ("from" in line) and (package_name in line):
                    # Replace old package name with the new one
                    new_line = line.replace(package_name, new_package_name)
                    new_content.append(new_line)
                    modified = True
                else:
                    new_content.append(line)

            if modified:
                with open(file_path, 'w', encoding = "utf-8") as file:
                    file.writelines(new_content)



    def rename_package(self, 
                       module_name : str = None,
                       new_module_name : str = None):

        """
        Rename package in PPR.
        """

        module_name = module_name.replace("-","_")
        new_module_name = new_module_name.replace("-","_")

        repo_paa_config_path = ".paa.config"

        paa_config = {}
        if self.paa_config:
            paa_config = self.paa_config

        if os.path.exists(repo_paa_config_path):
            with open(repo_paa_config_path, 'r', encoding = "utf-8") as file:
                repo_paa_config = yaml.safe_load(file) or {}

            paa_config.update(repo_paa_config)
        else:
            return 1

        for key, default_value in PAA_PATH_DEFAULTS.items():
            value = paa_config.get(key)
            if value is None:
                paa_config[key] = default_value
            elif isinstance(value, str) and value.strip() == "":
                paa_config[key] = default_value

        files_to_rename = {
            "main_module" : {
                "repo_path" : paa_config.get("module_dir"),
                "file_extension" : ".py"
            },
            "cli" : {
                "repo_path" : paa_config.get("cli_dir"),
                "file_extension" : ".py",
            },
            "mcp" : {
                "repo_path" : paa_config.get("mcp_dir"),
                "file_extension" : ".py",
            },
            "routes" : {
                "repo_path" : paa_config.get("api_routes_dir"),
                "file_extension" : ".py",
            },
            "streamlit" : {
                "repo_path" : paa_config.get("streamlit_dir"),
                "file_extension" : ".py",
            },
            "example_notebooks" : {
                "repo_path" : paa_config.get("example_notebooks_path"),
                "file_extension" : ".ipynb",
            },
            "drawio" : {
                "repo_path" : paa_config.get("drawio_dir"),
                "file_extension" : ".drawio"
            },
            "release_notes" : {
                "repo_path" : ".paa/release_notes",
                "file_extension" : ".md"
            },
            "pyproject" : {
                "repo_path" : ".paa/pyproject",
                "file_extension" : ".toml"
            }
        }

        dirs_to_rename = {
            "tests" : {
                "repo_dir" : paa_config.get("tests_dir"),

            },
            "artifacts" : {
                "repo_dir" : paa_config.get("artifacts_dir"),

            },
            "extra_docs" : {
                "repo_dir" : paa_config.get("extra_docs_dir"),

            },
            "skills" : {
                "repo_dir" : "skills",

            },
            "checkpoint_history" : {
                "repo_dir" : os.path.join(".paa", "history"),
            }
        }

        files_to_rename_imports = {
            "cli" : {
                "repo_path" : paa_config.get("cli_dir"),
            },
            "mcp" : {
                "repo_path" : paa_config.get("mcp_dir"),
            },
            "routes" : {
                "repo_path" : paa_config.get("api_routes_dir"),
            },
            "streamlit" : {
                "repo_path" : paa_config.get("streamlit_dir"),
            }
        }

        if not os.path.exists(".paa"):
            self.init_paa_dir()

        for file_name, file_spec in files_to_rename.items():

            self._rename_file(
                **file_spec,
                module_name = module_name,
                new_module_name = new_module_name,
                file_type = file_name
            )

        for dir_name, dir_spec in dirs_to_rename.items():

            self._rename_dirs(
                **dir_spec,
                module_name = module_name,
                new_module_name = new_module_name,
                dir_type = dir_name
            )

        for _, ftri in files_to_rename_imports.items():

            self._replace_package_name(
                **ftri,
                package_name = module_name,
                new_package_name = new_module_name
            )
    
