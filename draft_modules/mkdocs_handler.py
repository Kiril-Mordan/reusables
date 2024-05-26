import os
import shutil
import sys
import subprocess
import attr
import logging


@attr.s
class MkDocsHandler:

    # inputs
    package_name = attr.ib(type=str)
    docs_file_paths = attr.ib(type=list)

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

    def create_index(self, project_name: str = None):

      if project_name is None:
        project_name = self.package_name

      package_name = project_name.replace("_","-")

      content = f"""# Intro

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
