import os
import shutil
import sys
import subprocess
import attr
import logging
import codecs
import re
import requests
import nbformat
from nbconvert import MarkdownExporter
from nbconvert.preprocessors import ExecutePreprocessor

@attr.s
class LongDocHandler:

    notebook_path = attr.ib(default = None)
    markdown_filepath = attr.ib(default = None)
    timeout = attr.ib(default = 600, type = int)
    kernel_name = attr.ib(default = 'python', type = str)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='README Handler')
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

    def read_module_content(self,
                     filepath : str) -> str:

        """
        Method for reading in module.
        """

        with open(filepath, 'r') as file:
            return file.read()

    def extract_module_docstring(self,
                                 module_content : str) -> str:

        """
        Method for extracting title, module level docstring.
        """

        match = re.search(r'^("""(.*?)"""|\'\'\'(.*?)\'\'\')', module_content, flags=re.DOTALL)
        if match:
            docstring_content = match.group(2) if match.group(2) is not None else match.group(3)
            return docstring_content.strip()
        return None

    def _format_title(self, filename : str) -> str:
        """
        Formats the filename into a more readable title by removing the '.md' extension,
        replacing underscores with spaces, and capitalizing each word.
        """
        title_without_extension = os.path.splitext(filename)[0]  # Remove the .md extension
        title_with_spaces = title_without_extension.replace('_', ' ')  # Replace underscores with spaces
        # Capitalize the first letter of each word
        return ' '.join(word.capitalize() for word in title_with_spaces.split())

    def get_pypi_badge(self, module_name : str):

        """
        Get badge for module that was pushed to pypi.
        """

        # Convert underscores to hyphens
        module_name_hyphenated = module_name.replace('_', '-')
        pypi_module_link = f"https://pypi.org/project/{module_name_hyphenated}/"
        pypi_link = ""

        # Send a HEAD request to the PyPI module link
        response = requests.head(pypi_module_link)

        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            pypi_link = f"[![PyPiVersion](https://img.shields.io/pypi/v/{module_name_hyphenated})]({pypi_module_link})"

        return pypi_link


    def convert_notebook_to_md(self,
                               notebook_path : str = None,
                               output_path : str = None):

        """
        Convert example notebook to md without executing.
        """

        if notebook_path is None:
            notebook_path = self.notebook_path

        if output_path is None:
            output_path = self.markdown_filepath

        # Load the notebook
        with open(notebook_path, encoding='utf-8') as fh:
            notebook_node = nbformat.read(fh, as_version=4)

        # Create a Markdown exporter
        md_exporter = MarkdownExporter()

        # Process the notebook we loaded earlier
        (body, _) = md_exporter.from_notebook_node(notebook_node)

        # Write to the output markdown file
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(body)

        self.logger.debug(f"Converted {notebook_path} to {output_path}")

    def convert_and_execute_notebook_to_md(self,
                                           notebook_path : str = None,
                                           output_path : str = None,
                                           timeout : int = None,
                                           kernel_name: str = None):

        """
        Convert example notebook to md with executing.
        """

        if notebook_path is None:
            notebook_path = self.notebook_path

        if output_path is None:
            output_path = self.markdown_filepath

        if timeout is None:
            timeout = self.timeout

        if kernel_name is None:
            kernel_name = self.kernel_name

        # Load the notebook
        with open(notebook_path, encoding = 'utf-8') as fh:
            notebook_node = nbformat.read(fh, as_version=4)

        # Execute the notebook
        execute_preprocessor = ExecutePreprocessor(timeout=timeout, kernel_name=kernel_name)
        execute_preprocessor.preprocess(notebook_node, {'metadata': {'path': os.path.dirname(notebook_path)}})

        # Convert the notebook to Markdown
        md_exporter = MarkdownExporter()
        (body, _) = md_exporter.from_notebook_node(notebook_node)

        # Write to the output markdown file
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(body)

        self.logger.debug(f"Converted and executed {notebook_path} to {output_path}")

    def convert_dependacies_notebooks_to_md(self,
                                            dependacies_dir : str,
                                            dependacies_names : list,
                                            output_path : str = "../dep_md"):

        """
        Converts multiple dependacies into multiple md
        """

        for dep_name in dependacies_names:

            dependancy_path = os.path.join(dependacies_dir, dep_name + ".ipynb")

            self.convert_notebook_to_md(
                notebook_path = dependancy_path,
                output_path = os.path.join(output_path, f"{dep_name}.md")
            )

    def combine_md_files(self,
                         files_path : str,
                         md_files : list,
                         output_file : str,
                         content_section_title : str = "# Table of Contents\n"):
        """
        Combine all markdown (.md) files from the source directory into a single markdown file,
        and prepend a content section with a bullet point for each component.
        """
        # Ensure the source directory ends with a slash
        if not files_path.endswith('/'):
            files_path += '/'

        if md_files is None:
            # Get a list of all markdown files in the directory if not provided
            md_files = [f for f in os.listdir(files_path) if f.endswith('.md')]

        # Start with a content section
        content_section = content_section_title
        combined_content = ""

        for md_file in md_files:
            # Format the filename to a readable title for the content section
            title = self._format_title(md_file)
            # Add the title to the content section
            content_section += f"- {title}\n"

            with open(files_path + md_file, 'r', encoding='utf-8') as f:
                # Append each file's content to the combined_content string
                combined_content +=  f.read() + "\n\n"

        # Prepend the content section to the combined content
        final_content = content_section + "\n" + combined_content

        # Write the final combined content to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"Combined Markdown with Table of Contents written to {output_file}")

    def return_long_description(self,
                                markdown_filepath : str = None):

        """
        Return long descrition for review as txt.
        """

        if markdown_filepath is None:
            markdown_filepath = self.markdown_filepath

        with codecs.open(markdown_filepath, encoding="utf-8") as fh:
            long_description = "\n" + fh.read()

        return long_description


@attr.s
class MkDocsHandler:

    # inputs
    package_name = attr.ib(type=str)
    docs_file_paths = attr.ib(type=list)

    module_docstring = attr.ib(default=None, type=str)
    pypi_badge = attr.ib(default='', type=str)
    license_badge = attr.ib(default='', type=str)

    project_name = attr.ib(default="temp_project", type=str)

    # processed
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='MkDocs Handler')
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

    def create_mkdocs_project(self, project_name: str = None):
        """
        Create a new MkDocs project.
        """

        if project_name is None:
            project_name = self.project_name

        subprocess.run(["mkdocs", "new", project_name])
        print(f"Created new MkDocs project: {project_name}")

    def create_mkdocs_dir(self, project_name: str = None):
        """
        Create a new dir for MkDocs project.
        """

        if project_name is None:
            project_name = self.project_name

        if os.path.exists(project_name):
            shutil.rmtree(project_name)
        os.makedirs(project_name)

        print(f"Created new MkDocs dir: {project_name}")

    def move_files_to_docs(self, file_paths: dict = None, project_name: str = None):
        """
        Move files from given list of paths to the docs directory.
        """

        if file_paths is None:
            file_paths = self.docs_file_paths

        if project_name is None:
            project_name = self.project_name

        docs_dir = os.path.join(project_name, "docs")
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)

        for file_path in file_paths:
            if os.path.exists(file_path):
                filename = file_paths[file_path]
                destination = os.path.join(docs_dir, filename)

                # Ensure unique filenames
                if os.path.exists(destination):
                    base, extension = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(destination):
                        new_filename = f"{base}_{counter}{extension}"
                        destination = os.path.join(docs_dir, new_filename)
                        counter += 1

                shutil.copy(file_path, destination)
                print(f"Copied {file_path} to {destination}")
            else:
                print(f"File not found: {file_path}")

    def _clean_filename(self, filename: str, package_name: str) -> str:
        """
        Remove the package name prefix from the filename.

        Args:
            filename (str): The original filename.
            package_name (str): The package name to remove.

        Returns:
            str: The cleaned filename without the package name prefix.
        """
        if filename.startswith(f"{package_name}-"):
          return filename[len(package_name)+1:]
        # if filename == f"{package_name}.md":
        #   return "usage-examples.md"

        return filename

    def create_index(self,
                     project_name: str = None,
                     module_docstring : str = None,
                     pypi_badge : str = None,
                     license_badge : str = None):

        if project_name is None:
            project_name = self.package_name

        if module_docstring is None:
            module_docstring = self.module_docstring

        if pypi_badge is None:
            pypi_badge = self.pypi_badge

        if license_badge is None:
            license_badge = self.license_badge

        package_name = project_name.replace("_","-")

        content = f"""# Intro

{pypi_badge} {license_badge}

{module_docstring}

## Installation

```bash
pip install {package_name}
```
        """

        mkdocs_index_path = os.path.join("temp_project","docs", "index.md")
        with open(mkdocs_index_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"index.md has been created with site_name: {package_name}")



    def generate_markdown_for_images(self, package_name: str = None, project_name: str = None):
        """
        Generate .md files for each .png file in the specified directory based on naming rules.

        Args:
            directory (str): Path to the directory containing .png files.
            package_name (str): The package name to use for naming conventions.
        """

        if package_name is None:
            package_name = self.package_name

        if project_name is None:
            project_name = self.project_name

        directory = os.path.join(project_name, "docs")

        if not os.path.exists(directory):
            print(f"The directory {directory} does not exist.")
            return

        for filename in os.listdir(directory):
            if filename.endswith('.png'):
                cleaned_name = self._clean_filename(filename, package_name)
                md_filename = f"{os.path.splitext(cleaned_name)[0]}.md"

                md_filepath = os.path.join(directory, md_filename)

                # Write Markdown content
                with open(md_filepath, 'w') as md_file:
                    md_content = f"![{filename}](./{filename})"
                    md_file.write(md_content)
                print(f"Created {md_filepath}")

    def create_mkdocs_yml(self, package_name: str = None, project_name: str = None):
        """
        Create mkdocs.yml with a given site_name.
        """

        if project_name is None:
            project_name = self.project_name

        if package_name is None:
            package_name = self.package_name

        package_name = package_name.capitalize()
        package_name = package_name.replace("_"," ")

        content = f"""site_name: {package_name}

theme:
  name: material
  palette:
    # Palette toggle for light mode
    - scheme: default
      primary: green
      accent: green
      toggle:
        icon: material/lightbulb
        name: Switch to dark mode

    # Palette toggle for dark mode
    - scheme: slate
      primary: green
      accent: green
      toggle:
        icon: material/lightbulb-outline
        name: Switch to light mode

extra_css:
  - css/extra.css
        """

        mkdocs_yml_path = os.path.join(project_name, "mkdocs.yml")
        with open(mkdocs_yml_path, "w") as file:
            file.write(content.strip())
        print(f"mkdocs.yml has been created with site_name: {package_name}")

        css_dir = os.path.join(project_name, "docs", "css")
        if not os.path.exists(css_dir):
            os.makedirs(css_dir)

        css_content = """
/* Ensure tables are scrollable horizontally */
table {
  display: block;
  width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

/* Ensure tables and their parent divs don't overflow the content area */
.dataframe {
  display: block;
  width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

.dataframe thead th {
  text-align: right;
}

.dataframe tbody tr th {
  vertical-align: top;
}

.dataframe tbody tr th:only-of-type {
  vertical-align: middle;
}

/* Ensure the whole content area is scrollable */
.md-content__inner {
  overflow-x: auto;
  padding: 20px; /* Add some padding for better readability */
}

/* Fix layout issues caused by the theme */
.md-main__inner {
  max-width: none;
}
        """

        css_path = os.path.join(css_dir, "extra.css")
        with open(css_path, "w") as file:
            file.write(css_content.strip())
        print(f"Custom CSS created at {css_path}")

    def build_mkdocs_site(self, project_name: str = None):
        """
        Serve the MkDocs site.
        """

        if project_name is None:
            project_name = self.project_name

        os.chdir(project_name)
        subprocess.run(["mkdocs", "build"])
        os.chdir("..")

    def serve_mkdocs_site(self, project_name: str = None):
        """
        Serve the MkDocs site.
        """

        if project_name is None:
            project_name = self.project_name

        try:
            os.chdir(project_name)
            subprocess.run(["mkdocs", "serve"])
        except Exception as e:
            print(e)
        finally:
            os.chdir("..")



if __name__ == "__main__":

    package_name = sys.argv[1]

    module_content = LongDocHandler().read_module_content(filepath=f"python_modules/{package_name}.py")
    docstring = LongDocHandler().extract_module_docstring(module_content=module_content)
    pypi_link = LongDocHandler().get_pypi_badge(module_name=package_name)

    doc_files = os.listdir("docs")
    release_note_files = os.listdir("release_notes")

    docs_file_paths = {}

    package_docs = [doc_file for doc_file in doc_files if doc_file.startswith(package_name)]

    for package_doc in package_docs:

        if package_doc == f"{package_name}.md":
            docs_file_paths[os.path.join("docs",package_doc)] = "usage-examples.md"
        else:
            docs_file_paths[os.path.join("docs",package_doc)] = package_doc

    if f"{package_name}.md" in release_note_files:
        docs_file_paths[os.path.join("release_notes",f"{package_name}.md")] = "release-notes.md"


    mdh = MkDocsHandler(
        package_name = package_name,
        docs_file_paths = docs_file_paths,
        module_docstring = docstring,
        pypi_badge = pypi_link,
        license_badge="[![License](https://img.shields.io/github/license/Kiril-Mordan/reusables)](https://github.com/Kiril-Mordan/reusables/blob/main/LICENSE)")

    mdh.create_mkdocs_dir()
    mdh.move_files_to_docs()
    mdh.generate_markdown_for_images()
    mdh.create_index()
    mdh.create_mkdocs_yml()
    mdh.build_mkdocs_site()

    #mdh.serve_mkdocs_site()