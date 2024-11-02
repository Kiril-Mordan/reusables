import logging
import os
import codecs
from datetime import datetime
import re
import nbformat
from nbconvert import MarkdownExporter #==7.16.4
from nbconvert.preprocessors import ExecutePreprocessor
import attr #>=22.2.0
import requests

@attr.s
class LongDocHandler:

    """
    Contains set of tools to prepare package description.
    """

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

        pypi_link = ""

        try:

            # Convert underscores to hyphens
            module_name_hyphenated = module_name.replace('_', '-')
            pypi_module_link = f"https://pypi.org/project/{module_name_hyphenated}/"

            # Send a HEAD request to the PyPI module link
            response = requests.head(pypi_module_link)

            # Check if the response status code is 200 (OK)
            if response.status_code == 200:
                pypi_link = f"[![PyPiVersion](https://img.shields.io/pypi/v/{module_name_hyphenated})]({pypi_module_link})"
        except Exception as e:
            self.logger.warning("Pypi link not found!")
            
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

        if (notebook_path is not None) and os.path.exists(notebook_path):

            # Load the notebook
            with open(notebook_path, encoding='utf-8') as fh:
                notebook_node = nbformat.read(fh, as_version=4)

            # Create a Markdown exporter
            md_exporter = MarkdownExporter()

            # Process the notebook we loaded earlier
            (body, _) = md_exporter.from_notebook_node(notebook_node)

            self.logger.debug(f"Converted {notebook_path} to {output_path}")

        else:
            body = ""

        # Write to the output markdown file
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(body)



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

        if (notebook_path is not None) and os.path.exists(notebook_path):

            # Load the notebook
            with open(notebook_path, encoding = 'utf-8') as fh:
                notebook_node = nbformat.read(fh, as_version=4)

            # Execute the notebook
            execute_preprocessor = ExecutePreprocessor(timeout=timeout, kernel_name=kernel_name)
            execute_preprocessor.preprocess(notebook_node, {'metadata': {'path': os.path.dirname(notebook_path)}})

            # Convert the notebook to Markdown
            md_exporter = MarkdownExporter()
            (body, _) = md_exporter.from_notebook_node(notebook_node)

            self.logger.debug(f"Converted and executed {notebook_path} to {output_path}")

        else:

            body = ""

            # Write to the output markdown file
            with open(output_path, 'w', encoding='utf-8') as fh:
                fh.write(body)

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
        self.logger.debug(f"Combined Markdown with Table of Contents written to {output_file}")

    def get_referenced_images(self, md_file_path : str):

        """
        Extracts as list of image path referenced in the text file.
        """

        # Regex pattern to match image references in markdown files
        image_pattern = re.compile(r"!\[.*?\]\((.*?)\)")
        images = []

        if md_file_path and os.path.exists(md_file_path):

            # Open the markdown file and read its contents
            with open(md_file_path, 'r', encoding='utf-8') as md_file:
                content = md_file.read()

                # Find all image paths
                images = image_pattern.findall(content)

        images = [img for img in images if img.endswith(".png")]

        return images


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