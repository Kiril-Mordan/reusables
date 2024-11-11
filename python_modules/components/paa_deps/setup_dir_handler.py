import logging
import os
import shutil
import attr #>=22.2.0

@attr.s
class SetupDirHandler:

    """
    Contains set of tools to prepare setup directory for packaging.
    """

    module_filepath = attr.ib(type=str)
    module_name = attr.ib(default='', type=str)
    docstring = attr.ib(default=None, type=str)
    license_path = attr.ib(default=None, type=str)
    license_label = attr.ib(default=None, type=str)
    docs_url = attr.ib(default=None, type=str)
    metadata = attr.ib(default={}, type=dict)
    cli_metadata = attr.ib(default={}, type=dict)
    requirements = attr.ib(default=[], type=list)
    optional_requirements = attr.ib(default=None, type=list)
    classifiers = attr.ib(default=[], type=list)
    setup_directory = attr.ib(default='./setup_dir')
    add_cli_tool = attr.ib(default=False, type = bool)
    add_artifacts = attr.ib(default=False, type = bool)
    version = attr.ib(default=None, type = str)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Setup Dir Handler')
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

    def flush_n_make_setup_dir(self,
                               setup_directory : str = None):

        """
        Remove everything from a given directory or create a new one if doesn't exists already.
        """

        if setup_directory is None:
            setup_directory = self.setup_directory

        # Flushing setup directory
        if os.path.exists(setup_directory):
            shutil.rmtree(setup_directory)
        os.makedirs(setup_directory)


    def copy_module_to_setup_dir(self,
                                 module_filepath : str = None,
                                 setup_directory : str = None):

        """
        Copy module to new setup directory.
        """


        if module_filepath is None:
            module_filepath = self.module_filepath

        if setup_directory is None:
            setup_directory = self.setup_directory


        # Copying module to setup directory
        shutil.copy(module_filepath, setup_directory)

    def copy_license_to_setup_dir(self,
                                 license_path : str = None,
                                 setup_directory : str = None):

        """
        Copy module to new setup directory.
        """


        if license_path is None:
            license_path = self.license_path

        if setup_directory is None:
            setup_directory = self.setup_directory

        if license_path:
            # Copying module to setup directory
            shutil.copy(license_path, setup_directory)


    def create_init_file(self,
                         module_name : str = None,
                         docstring : str = None,
                         setup_directory : str = None,
                         version : str = None):

        """
        Create __init__.py for the package.
        """

        if module_name is None:
            if self.module_name == '':
                module_name = os.path.basename(self.module_filepath)
            else:
                module_name = self.module_name

        if setup_directory is None:
            setup_directory = self.setup_directory

        if docstring is None:
            docstring = self.docstring

        if version is None:
            version = self.version

        init_content = ''
        if docstring:
            init_content = f"""\n\"\"\"\n{docstring}\n\"\"\"\n"""
        init_content += f"""from .{module_name} import *\n"""
        if version:
            init_content += f"""__version__='{version}'"""

        # Creating temporary __init__.py file
        init_file_path = os.path.join(setup_directory, '__init__.py')
        with open(init_file_path, 'w') as init_file:
            init_file.write(init_content)

    def _prep_metadata_elem(self, key, value):

        if isinstance(value, str):
            return f'{key}="{value}"'
        else:
            return f'{key}={value}'

    def write_setup_file(self,
                         module_name : str = None,
                         module_docstring : str = None,
                         metadata : dict = None,
                         license_label : str = None,
                         docs_url : str = None,
                         cli_metadata : dict = None,
                         requirements : list = None,
                         optional_requirements : list = None,
                         classifiers : list = None,
                         setup_directory : str = None,
                         add_cli_tool : bool = None,
                         add_artifacts : bool = None,
                         artifacts_filepaths : dict = None):

        """
        Create setup.py for the package.
        """


        import pkg_resources

        if module_name is None:
            if self.module_name == '':
                module_name = os.path.basename(self.module_filepath)
            else:
                module_name = self.module_name

        if metadata is None:
            metadata = self.metadata

        if metadata is None:
            metadata = {}

        if cli_metadata is None:
            cli_metadata = self.cli_metadata

        if requirements is None:
            requirements = self.requirements

        if requirements is None:
            requirements = []
        else:
            requirements = [req for req in requirements if not req.startswith("###")]

        if optional_requirements is None:
            optional_requirements = self.optional_requirements

        if classifiers is None:
            classifiers = self.classifiers

        if license_label is None:
            license_label = self.license_label

        if docs_url is None:
            docs_url = self.docs_url

        if add_cli_tool is None:
            add_cli_tool = self.add_cli_tool

        if add_artifacts is None:
            add_artifacts = self.add_artifacts

        paa_version = pkg_resources.get_distribution("package_auto_assembler").version

        if classifiers is None:
            classfiers = []
            #classifiers = [f"PAA-Version :: {paa_version}"]
        # else:
        #     classifiers.append(f"PAA-Version :: {paa_version}")

        #classifiers.append(f"PAA-CLI :: {add_cli_tool}")

        development_statuses = [
            "Development Status :: 1 - Planning",
            "Development Status :: 2 - Pre-Alpha",
            "Development Status :: 3 - Alpha",
            "Development Status :: 4 - Beta",
            "Development Status :: 5 - Production/Stable",
            "Development Status :: 6 - Mature",
            "Development Status :: 7 - Inactive"]

        if 'classifiers' in metadata.keys():

            metadata_classifiers = metadata['classifiers'] 

            if any([mc.startswith("Development Status") for mc in metadata_classifiers]):
                classifiers = [c for c in classifiers if not c.startswith("Development Status")]
                
            classifiers+=metadata_classifiers

            del metadata['classifiers']

        if setup_directory is None:
            setup_directory = self.setup_directory

        extras_require = None

        if optional_requirements:

            extras_require = {req.split("=")[0].split("<")[0] : [req] for req in optional_requirements}
            extras_require['all'] = optional_requirements

        if 'extras_require' in metadata.keys():

            if extras_require is None:
                extras_require = {}

            extras_require.update(metadata['extras_require'])
            del metadata['extras_require']

        if 'install_requires' in metadata.keys():
            requirements+=metadata['install_requires']
            del metadata['install_requires']

    
        metadata_str = None
        metadata_str = ',\n    '.join([self._prep_metadata_elem(key, value) \
            for key, value in metadata.items()])


        title = module_name.capitalize()
        title = title.replace("_"," ")

        long_description_intro = f"""# {title}\n\n"""

        if module_docstring:
            long_description_intro += f"""{module_docstring}\n\n"""


        if add_cli_tool:
            entry_points = {
                'console_scripts': [
                    f'{module_name} = {module_name}.cli:cli',
                ]
            }

            if "name" in cli_metadata.keys():
                entry_points = {
                'console_scripts': [
                    f"{cli_metadata['name']} = {module_name}.cli:cli",
                ]
            }

        ###

        setup_content = "from setuptools import setup\n\n"

        setup_content += "import codecs\n"
        setup_content += "import os\n\n"

        setup_content += "here = os.path.abspath(os.path.dirname(__file__))\n"
        setup_content += 'path_to_readme = os.path.join(here, "README.md")\n\n'

        setup_content += f'long_description = """{long_description_intro}"""'

        setup_content += f"""

if os.path.exists(path_to_readme):
  with codecs.open(path_to_readme, encoding="utf-8") as fh:
      long_description += fh.read()

setup(
    name="{module_name}",
    packages=["{module_name}"],
    install_requires={requirements},
    classifiers={classifiers},
    long_description=long_description,
    long_description_content_type='text/markdown',
"""
        if metadata_str:
            setup_content += f"""    {metadata_str},"""

        if add_cli_tool:
            setup_content += f"""
    entry_points = {entry_points},
"""
        if extras_require:
            setup_content += f"""
    extras_require = {extras_require},
"""
        if license_label and ('license' not in metadata.keys()):
            setup_content += f"""
    license = "{license_label}",
"""

        if docs_url and ('url' not in metadata.keys()):
            setup_content += f"""    url = {docs_url},
"""

        if add_artifacts and artifacts_filepaths != {}:
            setup_content += f"""    include_package_data = True,
"""

            package_data = {
                f"{module_name}" : [art for art in artifacts_filepaths],
            }
            setup_content += f"""    package_data = {package_data} ,
"""

        setup_content += f"""    )
"""

        with open(os.path.join(setup_directory, 'setup.py'), 'w') as file:
            file.write(setup_content)