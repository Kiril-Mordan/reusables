import logging
import os
import shutil
import copy
import importlib.metadata
import attrs
import attrsx

@attrsx.define
class SetupDirHandler:

    """
    Contains set of tools to prepare setup directory for packaging.

    Usage example:
    ```python
    sdh = SetupDirHandler(
        module_filepath="python_modules/your_package.py",
        module_name="your_package",
        setup_directory="./your_package",
        requirements=["attrsx>=0.0.9"],
    )
    sdh.flush_n_make_setup_dir()
    sdh.copy_module_to_setup_dir()
    sdh.create_init_file()
    sdh.write_setup_file()
    ```
    """

    module_filepath = attrs.field(type=str)
    module_name = attrs.field(default='', type=str)
    docstring = attrs.field(default=None, type=str)
    license_path = attrs.field(default=None, type=str)
    notice_path = attrs.field(default=None, type=str)
    license_label = attrs.field(default=None, type=str)
    docs_url = attrs.field(default=None, type=str)
    metadata = attrs.field(default={}, type=dict)
    cli_metadata = attrs.field(default={}, type=dict)
    requirements = attrs.field(default=[], type=list)
    optional_requirements = attrs.field(default=None, type=list)
    classifiers = attrs.field(default=[], type=list)
    setup_directory = attrs.field(default='./setup_dir')
    pyproject_directory = attrs.field(default='./.paa/pyproject')
    add_cli_tool = attrs.field(default=False, type = bool)
    add_artifacts = attrs.field(default=False, type = bool)
    version = attrs.field(default=None, type = str)

    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Package Setup Dir Handler')
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

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
            shutil.copy(license_path, os.path.join(setup_directory, "LICENSE"))

    def copy_notice_to_setup_dir(self,
                                 notice_path : str = None,
                                 setup_directory : str = None):

        """
        Copy NOTICE file to setup directory.
        """

        if notice_path is None:
            notice_path = self.notice_path

        if setup_directory is None:
            setup_directory = self.setup_directory

        if notice_path:
            shutil.copy(notice_path, os.path.join(setup_directory, "NOTICE"))


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

        paa_version = importlib.metadata.version("package_auto_assembler")

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

        setup_content += """    license_files = [\"LICENSE\", \"NOTICE\"],
"""

        setup_content += f"""    )
"""

        with open(os.path.join(setup_directory, 'setup.py'), 'w') as file:
            file.write(setup_content)

    def _toml_string(self, value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def _toml_key(self, key):
        escaped = str(key).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def _toml_list(self, values):
        return "[" + ", ".join(self._toml_string(v) for v in values) + "]"

    def _toml_list_pretty(self, values, multiline_threshold: int = 4):
        normalized = [str(v) for v in values]
        if len(normalized) <= multiline_threshold:
            return self._toml_list(normalized)

        body = ",\n".join(f"  {self._toml_string(v)}" for v in normalized)
        return "[\n" + body + "\n]"

    def _toml_inline_table(self, values: dict):
        items = [f'{k} = {self._toml_string(v)}' for k, v in values.items()]
        return "{ " + ", ".join(items) + " }"

    def _dedupe_and_sort_list(self, values):
        cleaned = [str(v) for v in values if str(v).strip()]
        return sorted(set(cleaned), key=lambda x: x.lower())

    def write_pyproject_file(self,
                             module_name : str = None,
                             metadata : dict = None,
                             license_label : str = None,
                             docs_url : str = None,
                             cli_metadata : dict = None,
                             requirements : list = None,
                             optional_requirements : list = None,
                             classifiers : list = None,
                             add_cli_tool : bool = None,
                             pyproject_directory : str = None):

        """
        Create per-package pyproject toml metadata file.
        """

        if module_name is None:
            if self.module_name == '':
                module_name = os.path.basename(self.module_filepath)
            else:
                module_name = self.module_name

        metadata = copy.deepcopy(metadata if metadata is not None else self.metadata)
        cli_metadata = copy.deepcopy(cli_metadata if cli_metadata is not None else self.cli_metadata)

        if requirements is None:
            requirements = self.requirements
        if requirements is None:
            requirements = []
        requirements = [req for req in requirements if not req.startswith("###")]
        requirements = self._dedupe_and_sort_list(requirements)

        if optional_requirements is None:
            optional_requirements = self.optional_requirements
        if optional_requirements is None:
            optional_requirements = []
        optional_requirements = self._dedupe_and_sort_list(optional_requirements)

        if classifiers is None:
            classifiers = self.classifiers
        if classifiers is None:
            classifiers = []
        classifiers = self._dedupe_and_sort_list(classifiers)

        if license_label is None:
            license_label = self.license_label
        if docs_url is None:
            docs_url = self.docs_url
        if add_cli_tool is None:
            add_cli_tool = self.add_cli_tool
        if pyproject_directory is None:
            pyproject_directory = self.pyproject_directory

        project_name = metadata.get("name", module_name.replace("_", "-"))
        description = metadata.get("description", "")
        readme = metadata.get("readme", "README.md")
        requires_python = metadata.get("requires_python", ">=3.8")

        combined_classifiers = list(classifiers)
        metadata_classifiers = metadata.get("classifiers")
        if isinstance(metadata_classifiers, list):
            if any(c.startswith("Development Status") for c in metadata_classifiers):
                combined_classifiers = [c for c in combined_classifiers if not c.startswith("Development Status")]
            combined_classifiers += metadata_classifiers

        keywords = metadata.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]
        keywords = self._dedupe_and_sort_list(keywords)

        authors = []
        author_name = metadata.get("author")
        author_email = metadata.get("author_email")
        if author_name or author_email:
            author_item = {}
            if author_name:
                author_item["name"] = author_name
            if author_email:
                author_item["email"] = author_email
            authors.append(author_item)

        urls = {}
        if metadata.get("url"):
            urls["Homepage"] = metadata["url"]
        if docs_url:
            urls["Documentation"] = docs_url
        if metadata.get("project_urls") and isinstance(metadata["project_urls"], dict):
            urls.update(metadata["project_urls"])

        entry_points = {}
        if add_cli_tool:
            script_name = cli_metadata.get("name", module_name)
            entry_points = {script_name: f"{module_name}.cli:cli"}

        optional_deps = {}
        if optional_requirements:
            optional_deps = {
                req.split("=")[0].split("<")[0].strip(): [req]
                for req in optional_requirements
            }
            optional_deps["all"] = optional_requirements

        if metadata.get("extras_require") and isinstance(metadata["extras_require"], dict):
            for key, value in metadata["extras_require"].items():
                optional_deps[key] = value if isinstance(value, list) else [str(value)]

        os.makedirs(pyproject_directory, exist_ok=True)
        pyproject_path = os.path.join(pyproject_directory, f"{module_name}.toml")

        lines = []
        lines.append("[build-system]")
        lines.append('requires = ["setuptools>=61.0", "wheel"]')
        lines.append('build-backend = "setuptools.build_meta"')
        lines.append("")
        lines.append("[project]")
        lines.append(f"name = {self._toml_string(project_name)}")
        if self.version:
            lines.append(f"version = {self._toml_string(self.version)}")
        lines.append(f"description = {self._toml_string(description)}")
        lines.append(f"readme = {self._toml_string(readme)}")
        lines.append(f"requires-python = {self._toml_string(requires_python)}")

        if keywords:
            lines.append(f"keywords = {self._toml_list_pretty(keywords)}")
        if combined_classifiers:
            lines.append(f"classifiers = {self._toml_list_pretty(combined_classifiers)}")
        if requirements:
            lines.append(f"dependencies = {self._toml_list_pretty(requirements)}")
        if authors:
            authors_inline = ", ".join(self._toml_inline_table(a) for a in authors)
            lines.append(f"authors = [{authors_inline}]")

        if license_label:
            lines.append(f'license = {{ text = "{license_label}" }}')

        if urls:
            lines.append("")
            lines.append("[project.urls]")
            for key, value in urls.items():
                lines.append(f"{self._toml_key(key)} = {self._toml_string(str(value))}")

        if entry_points:
            lines.append("")
            lines.append("[project.scripts]")
            for key, value in entry_points.items():
                lines.append(f"{key} = {self._toml_string(value)}")

        if optional_deps:
            lines.append("")
            lines.append("[project.optional-dependencies]")
            for key, value in optional_deps.items():
                deduped_optional = self._dedupe_and_sort_list(value)
                lines.append(f"{self._toml_key(key)} = {self._toml_list_pretty(deduped_optional)}")

        lines.append("")
        lines.append("[tool.setuptools]")
        lines.append('license-files = ["LICENSE", "NOTICE"]')

        with open(pyproject_path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")
