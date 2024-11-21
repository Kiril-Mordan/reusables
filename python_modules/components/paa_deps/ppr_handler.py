import logging
import os
import subprocess
import importlib
import importlib.metadata
import importlib.resources as pkg_resources
import csv
import shutil
import yaml
import attr #>=22.2.0

@attr.s
class PprHandler:

    """
    Prepares and handles python packaging repo with package-auto-assembler.
    """

    # inputs
    paa_dir = attr.ib(default=".paa")
    paa_config_file = attr.ib(default=".paa.config")

    init_dirs = attr.ib(default=["module_dir", "example_notebooks_path",
            "dependencies_dir", "cli_dir", "api_routes_dir", "streamlit_dir",
            "artifacts_dir", "drawio_dir", "extra_docs_dir", "tests_dir"])

    module_dir = attr.ib(default=None)
    drawio_dir = attr.ib(default=None)
    docs_dir = attr.ib(default=None)

    pylint_threshold = attr.ib(default=None)

    # processed
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='PPR Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

    def _initialize_logger(self):
        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

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

        with open(os.path.join(paa_dir,'tracking','lsts_package_versions.yml'),
            'w') as file:
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

    def init_from_paa_config(self, default_config : dict):

        config = self.paa_config_file
        init_dirs = self.init_dirs

        if os.path.exists(config):
            with open(config, 'r') as file:
                paa_config = yaml.safe_load(file)

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
                "api_routes_dir" : py_ignore,
                "streamlit_dir" : py_ignore,
                "drawio_dir" : drawio_ignore

            }

            for d in init_dirs:

                if paa_config.get(d):
                    if not os.path.exists(paa_config.get(d)):
                        os.makedirs(paa_config.get(d))
                    else:
                        self.logger.warning(f"{paa_config.get(d)} already exists!")

                    gitignore_path = os.path.join(paa_config.get(d), '.gitignore')

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
                yaml.dump(default_config, file, sort_keys=False)

        


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
                other_files = ['tox.ini', '.pylintrc']
            else:
                other_files = [ '.pylintrc']

            if not os.path.exists(template_path):

                # if workflows_platform == 'azure':
                #     self.logger.warning(
                #     "Template for azure devops pipeline will be available in future paa releases!")

                return False

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

                if os.path.exists(artifact_path):
                    if not os.path.exists(f):
                        shutil.copy(artifact_path, f)

            return True

        return False
