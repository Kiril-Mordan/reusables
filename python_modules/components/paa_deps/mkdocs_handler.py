import logging
import os
import subprocess
import shutil
import re
import attrs #>=22.2.0

#@ mkdocs>=1.6.0
#@ mkdocs-material>=9.5.30
#@ mkdocs-mermaid2-plugin>=1.2.1

@attrs.define
class MkDocsHandler:

    """
    Contains set of tools to use mkdocs to prepare package documentation.
    """

    # inputs
    package_name = attrs.field(type=str)
    docs_file_paths = attrs.field(type=list)

    module_docstring = attrs.field(default=None, type=str)
    pypi_badge = attrs.field(default='', type=str)
    license_badge = attrs.field(default='', type=str)

    project_name = attrs.field(default="temp_project", type=str)

    # processed
    logger = attrs.field(default=None)
    logger_name = attrs.field(default='MkDocs Handler')
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

    def create_mkdocs_project(self, project_name: str = None):
        """
        Create a new MkDocs project.
        """

        if project_name is None:
            project_name = self.project_name

        subprocess.run(["mkdocs", "new", project_name], check=True)
        self.logger.debug(f"Created new MkDocs project: {project_name}")

    def create_mkdocs_dir(self, project_name: str = None):
        """
        Create a new dir for MkDocs project.
        """

        if project_name is None:
            project_name = self.project_name

        if os.path.exists(project_name):
            shutil.rmtree(project_name)
        os.makedirs(project_name)

        self.logger.debug(f"Created new MkDocs dir: {project_name}")


    def _replace_image_paths(self,
                            md_file_path : str,
                            new_md_file_path : str,
                            path_replacements : dict):

        # Regex pattern to match image paths
        image_pattern = re.compile(r"(!\[.*?\]\()(.*?)(\))")

        # Read the markdown file content
        with open(md_file_path, 'r', encoding='utf-8') as md_file:
            content = md_file.read()

        # Replace image paths using the provided path replacements dictionary
        def replace_match(match):
            original_path = match.group(2)
            # Replace only if the original path is in path_replacements
            new_path = path_replacements.get(original_path, original_path)
            return f"{match.group(1)}{new_path}{match.group(3)}"

        updated_content = image_pattern.sub(replace_match, content)

        # Write the updated content to a new markdown file
        with open(new_md_file_path, 'w', encoding='utf-8') as new_md_file:
            new_md_file.write(updated_content)

        self.logger.debug(f"Image paths replaced and written to: {new_md_file_path}")

    def move_files_to_docs(self,
                           file_paths: dict = None,
                           project_name: str = None,
                           package_name: str = None,
                           image_path_replacements : dict = {}):
        """
        Move files from given list of paths to the docs directory.
        """

        if file_paths is None:
            file_paths = self.docs_file_paths

        if project_name is None:
            project_name = self.project_name

        if package_name is None:
            package_name = self.package_name

        docs_dir = os.path.join(project_name, "docs")
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)

        if not os.path.exists(os.path.join(docs_dir, "images")):
            os.makedirs(os.path.join(docs_dir, "images"))

        for file_path in file_paths:
            if os.path.exists(file_path):
                filename = file_paths[file_path]
                cleaned_filename = self._clean_filename(
                            filename, package_name)
                destination = os.path.join(docs_dir, cleaned_filename)

                # Ensure unique filenames
                if os.path.exists(destination):
                    base, extension = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(destination):
                        new_filename = f"{base}_{counter}{extension}"
                        destination = os.path.join(docs_dir, new_filename)
                        counter += 1

                if destination.endswith(".md"):
                    self._replace_image_paths(
                        md_file_path = file_path,
                        new_md_file_path = destination,
                        path_replacements = image_path_replacements
                    )
                elif os.path.isdir(file_path):

                    shutil.copytree(file_path, destination)

                    subfolder_mds = os.listdir(destination)

                    for file in subfolder_mds:
                        if file.endswith(".md"):
                            self._replace_image_paths(
                                md_file_path = os.path.join(destination, file),
                                new_md_file_path = os.path.join(destination, file),
                                path_replacements = image_path_replacements
                            )

                else:
                    shutil.copy(file_path, destination)

                self.logger.debug(f"Copied {file_path} to {destination}")
            else:
                self.logger.warning(f"File not found: {file_path}")

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

        return filename

    def create_index(self,
                     package_name: str = None,
                     project_name: str = None,
                     module_docstring : str = None,
                     pypi_badge : str = None,
                     license_badge : str = None):

        """
        Create index page with small intro.
        """

        if project_name is None:
            project_name = self.project_name

        if module_docstring is None:
            module_docstring = self.module_docstring

        if module_docstring is None:
            module_docstring = ''

        if pypi_badge is None:
            pypi_badge = self.pypi_badge

        if pypi_badge is None:
            pypi_badge = ''

        if license_badge is None:
            license_badge = self.license_badge

        if license_badge is None:
            license_badge = ''

        if package_name is None:
            package_name = self.package_name

        content = f"""# Intro

{pypi_badge} {license_badge}

{module_docstring}

"""


        if pypi_badge != '':
            content += f"""
## Installation

```bash
pip install {package_name.replace("_", "-")}
```

"""

        mkdocs_index_path = os.path.join(project_name,"docs", "index.md")
        with open(mkdocs_index_path, 'w', encoding='utf-8') as file:
            file.write(content)
        self.logger.debug(f"index.md has been created with site_name: {package_name}")



    def generate_markdown_for_images(self,
        package_name: str = None,
        project_name: str = None):
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
            self.logger.warning(f"The directory {directory} does not exist.")
            return

        for filename in os.listdir(directory):

            if filename.endswith('.png'):
                cleaned_name = self._clean_filename(filename, package_name)
                md_filename = f"{os.path.splitext(cleaned_name)[0]}.md"

                md_filepath = os.path.join(directory, md_filename)

                # Write Markdown content
                with open(md_filepath, 'w', encoding = "utf-8") as md_file:
                    md_content = f"![{filename}](./{filename})"
                    md_file.write(md_content)
                self.logger.debug(f"Created {md_filepath}")


    def _generate_nav_entries(self, base_path: str, indent: int = 2):
        nav_entries = []
        # List all files and directories at the base level
        for entry in os.listdir(base_path):

            if entry in ['css', 'images','index.md']:
                continue

            entry_path = os.path.join(base_path, entry)

            # Process files directly in the base directory
            if os.path.isfile(entry_path) and entry.endswith(".md"):
                file_name = os.path.splitext(entry)[0].replace("_", " ").replace("-", " ")
                file_indent = " " * indent
                nav_entries.append(f"{file_indent}- {file_name.capitalize()}: {entry}")

            # Process subdirectories
            elif os.path.isdir(entry_path):
                md_files = [f for f in os.listdir(entry_path) if f.endswith(".md")]

                # Add subfolder as a section in nav
                section_indent = " " * indent
                nav_entries.append(f"{section_indent}- {entry.capitalize()}: ")

                # Copy files from subfolder to base path but structure in nav as if in folder
                for md_file in md_files:
                    src_path = os.path.join(entry_path, md_file)
                    dest_path = os.path.join(base_path, md_file)
                    shutil.copy(src_path, dest_path)
                    file_indent = " " * (indent + 2)
                    file_name = os.path.splitext(md_file)[0].replace("_", " ").replace("-", " ")
                    nav_entries.append(f"{file_indent}- {file_name.capitalize()}: {md_file}")

                shutil.rmtree(entry_path)

        return "\n".join(nav_entries) if nav_entries else None


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

plugins:
  - mermaid2
  - search

extra_css:
  - css/extra.css

        """

        nav_content = self._generate_nav_entries(os.path.join(project_name, "docs"))

        if nav_content:
            content += f"""
nav:
  - Intro: index.md
{nav_content}
            """

        mkdocs_yml_path = os.path.join(project_name, "mkdocs.yml")
        with open(mkdocs_yml_path, "w", encoding = "utf-8") as file:
            file.write(content.strip())
        self.logger.debug(f"mkdocs.yml has been created with site_name: {package_name}")

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
        with open(css_path, "w", encoding = "utf-8") as file:
            file.write(css_content.strip())
        self.logger.debug(f"Custom CSS created at {css_path}")

    def build_mkdocs_site(self, project_name: str = None):
        """
        Serve the MkDocs site.
        """

        if project_name is None:
            project_name = self.project_name

        os.chdir(project_name)
        subprocess.run(["mkdocs", "build"], check=True)
        os.chdir("..")

    def serve_mkdocs_site(self, project_name: str = None):
        """
        Serve the MkDocs site.
        """

        if project_name is None:
            project_name = self.project_name

        try:
            os.chdir(project_name)
            subprocess.run(["mkdocs", "serve"], check=True)
        except Exception as e:
            print(e)
        finally:
            os.chdir("..")