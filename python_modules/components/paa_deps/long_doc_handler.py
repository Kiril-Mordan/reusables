import logging
import os
import codecs
from datetime import datetime
import re
import shutil
import copy
import json
import nbformat
from nbconvert import MarkdownExporter #>=7.16.4
from nbconvert.preprocessors import ExecutePreprocessor
import attrs #>=22.2.0
import attrsx
import requests
import base64

#@ jupyter>=1.1.1


@attrsx.define
class LongDocHandler:

    """
    Contains set of tools to prepare package description.
    """

    module_name = attrs.field(default = None)
    notebook_path = attrs.field(default = None)
    markdown_filepath = attrs.field(default = None)
    timeout = attrs.field(default = 600, type = int)
    kernel_name = attrs.field(default = 'python', type = str)
    hide_code_cell_prefixes = attrs.field(default=("#| paa-hide-code", "#| hide-code"))

    logger = attrs.field(default=None)
    logger_name = attrs.field(default='README Handler')
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
            response = requests.head(pypi_module_link, timeout=self.timeout)

            # Check if the response status code is 200 (OK)
            if response.status_code == 200:
                pypi_link = f"[![PyPiVersion](https://img.shields.io/pypi/v/{module_name_hyphenated})]({pypi_module_link})"
        except Exception as e:
            self.logger.warning("Pypi link not found!")

        return pypi_link

    def _to_markdown_path(self, path: str) -> str:
        """
        Normalize generated markdown paths to POSIX separators.
        """

        return path.replace("\\", "/")

    def _extract_pngs_and_patch_md(self,
                                   notebook_node,
                                   md_text: str,
                                   output_path: str,
                                   image_output_dir: str = None) -> str:
        """
        Extract image/png outputs from a notebook and save them next to output_path.
        Patch markdown so any nbconvert-style refs like output_{cell}_{out}.png
        point to the actual extracted filenames.
        """
        markdown_dir = os.path.dirname(output_path)
        out_dir = image_output_dir or markdown_dir
        out_dir = os.path.abspath(out_dir)
        markdown_dir = os.path.abspath(markdown_dir)
        os.makedirs(out_dir, exist_ok=True)

        # Find synthetic refs in markdown produced by MarkdownExporter
        synthetic_refs = set(re.findall(r"\boutput_\d+_\d+\.png\b", md_text))

        replacements = {}  # synthetic -> actual
        for cell_i, cell in enumerate(notebook_node.get("cells", [])):
            for out_i, out in enumerate(cell.get("outputs", [])):
                data = out.get("data") if isinstance(out, dict) else None
                if not isinstance(data, dict):
                    continue

                png_b64 = data.get("image/png")
                if not png_b64:
                    continue

                # Deterministic, collision-free filename with notebook marker.
                module_prefix = self.module_name if self.module_name else "notebook"
                actual_name = f"{module_prefix}_ipynb_cell{cell_i}_out{out_i}.png"
                actual_path = os.path.join(out_dir, actual_name)

                # Write bytes
                with open(actual_path, "wb") as f:
                    f.write(base64.b64decode(png_b64))

                # If markdown references the synthetic name, map it
                synthetic_name = f"output_{cell_i}_{out_i}.png"
                if synthetic_name in synthetic_refs:
                    replacements[synthetic_name] = self._to_markdown_path(
                        os.path.relpath(actual_path, start=markdown_dir)
                    )

        # Patch markdown
        for old, new in replacements.items():
            md_text = md_text.replace(old, new)

        return md_text


    def _export_md_without_nbconvert_extraction(self, notebook_node, output_path: str) -> str:
        """
        Export notebook to markdown using MarkdownExporter (no ExtractOutputPreprocessor).
        Returns markdown text.
        """
        md_exporter = MarkdownExporter()
        md_text, _ = md_exporter.from_notebook_node(notebook_node)
        return md_text

    def _should_hide_code_cell(self, source: str) -> bool:

        if not source:
            return False

        first_non_empty = None
        for line in str(source).splitlines():
            candidate = line.strip()
            if candidate:
                first_non_empty = candidate
                break

        if not first_non_empty:
            return False

        return any(first_non_empty.startswith(prefix) for prefix in self.hide_code_cell_prefixes)

    def _prepare_notebook_for_markdown(self, notebook_node):

        prepared = copy.deepcopy(notebook_node)
        filtered_cells = []

        for cell in prepared.get("cells", []):
            if cell.get("cell_type") != "code":
                filtered_cells.append(cell)
                continue

            if self._should_hide_code_cell(cell.get("source", "")):
                outputs = cell.get("outputs", [])
                if outputs:
                    # Keep outputs, hide input code block in markdown output.
                    cell["source"] = ""
                    filtered_cells.append(cell)
                # Drop tagged code cell entirely when there is no output.
                continue

            filtered_cells.append(cell)

        prepared["cells"] = filtered_cells
        return prepared

    def _load_notebook_node(self, notebook_path: str):
        """
        Load notebook with backward-compat handling for older nbformat schemas
        that reject cell-level ``id`` fields.
        """
        with open(notebook_path, encoding="utf-8") as fh:
            raw = fh.read()

        try:
            return nbformat.reads(raw, as_version=4)
        except Exception:
            notebook_data = json.loads(raw)
            if isinstance(notebook_data, dict):
                for cell in notebook_data.get("cells", []):
                    if isinstance(cell, dict):
                        cell.pop("id", None)
            return nbformat.from_dict(notebook_data)


    def convert_notebook_to_md(self,
                               notebook_path: str = None,
                               output_path: str = None,
                               image_output_dir: str = None):
        """
        Convert notebook to markdown WITHOUT executing.
        Also extracts any image/png outputs as files next to the markdown.
        """
        if notebook_path is None:
            notebook_path = self.notebook_path
        if output_path is None:
            output_path = self.markdown_filepath

        if (notebook_path is not None) and os.path.exists(notebook_path):
            notebook_node = self._load_notebook_node(notebook_path)

            notebook_for_export = self._prepare_notebook_for_markdown(notebook_node)

            md_text = self._export_md_without_nbconvert_extraction(notebook_for_export, output_path)
            md_text = self._extract_pngs_and_patch_md(
                notebook_for_export,
                md_text,
                output_path,
                image_output_dir=image_output_dir
            )

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(md_text)

            self.logger.debug(f"Converted {notebook_path} to {output_path} (with extracted images)")
        else:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write("")




    def convert_and_execute_notebook_to_md(
        self,
        notebook_path: str = None,
        output_path: str = None,
        image_output_dir: str = None,
        timeout: int = None,
        kernel_name: str = None,
    ):
        """
        Execute notebook, convert to markdown, and extract image/png outputs next to the markdown.
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
            notebook_node = self._load_notebook_node(notebook_path)

            execute_preprocessor = ExecutePreprocessor(timeout=timeout, kernel_name=kernel_name)
            execute_preprocessor.preprocess(
                notebook_node,
                {"metadata": {"path": os.path.dirname(notebook_path)}},
            )

            notebook_for_export = self._prepare_notebook_for_markdown(notebook_node)

            md_text = self._export_md_without_nbconvert_extraction(notebook_for_export, output_path)
            md_text = self._extract_pngs_and_patch_md(
                notebook_for_export,
                md_text,
                output_path,
                image_output_dir=image_output_dir
            )

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(md_text)

            self.logger.debug(f"Converted+executed {notebook_path} to {output_path} (with extracted images)")
        else:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write("")


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

    def prep_extra_docs(self,
                        package_name : str,
                        extra_docs_dir : str,
                        docs_path : str):

        """
        Prepares extra docs for packaging.
        """

        if extra_docs_dir and os.path.exists(extra_docs_dir):

            os.makedirs(docs_path, exist_ok=True)
            files = os.listdir(extra_docs_dir)

            for f in files:
                source_path = os.path.join(extra_docs_dir, f)
                destination_path = os.path.join(docs_path, f"{package_name}-{f}")

                if os.path.exists(destination_path):
                    if os.path.isdir(destination_path):
                        shutil.rmtree(destination_path)
                    else:
                        os.remove(destination_path)

                self._copy_extra_docs_item(
                    source_path=source_path,
                    destination_path=destination_path
                )

    def _copy_extra_docs_item(self,
                              source_path: str,
                              destination_path: str,
                              docs_root_path: str = None):

        if not os.path.exists(source_path):
            return

        if docs_root_path is None:
            docs_root_path = destination_path if os.path.isdir(destination_path) else os.path.dirname(destination_path)

        if os.path.isdir(source_path):
            os.makedirs(destination_path, exist_ok=True)
            for item_name in os.listdir(source_path):
                self._copy_extra_docs_item(
                    source_path=os.path.join(source_path, item_name),
                    destination_path=os.path.join(destination_path, item_name),
                    docs_root_path=docs_root_path
                )
            return

        if source_path.endswith(".ipynb"):
            output_path = destination_path.replace(".ipynb", ".md")
            self.convert_notebook_to_md(
                notebook_path=source_path,
                output_path=output_path,
                image_output_dir=os.path.dirname(os.path.dirname(destination_path))
            )
            return

        if source_path.endswith(".md") or source_path.endswith(".png"):
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            if source_path.endswith(".md"):
                self._copy_markdown_with_root_image_refs(
                    source_path=source_path,
                    destination_path=destination_path,
                    docs_root_path=docs_root_path
                )
            else:
                shutil.copy(source_path, destination_path)

    def _copy_markdown_with_root_image_refs(self,
                                            source_path: str,
                                            destination_path: str,
                                            docs_root_path: str):

        with open(source_path, "r", encoding="utf-8") as md_file:
            content = md_file.read()

        image_pattern = re.compile(r"(!\[.*?\]\()(.*?)(\))")
        destination_dir = os.path.dirname(os.path.abspath(destination_path))
        docs_root_path = os.path.abspath(docs_root_path)

        def replace_match(match):
            original_path = match.group(2)

            if os.path.isabs(original_path) or "://" in original_path:
                return match.group(0)

            candidate_in_destination = os.path.normpath(os.path.join(destination_dir, original_path))
            candidate_in_root = os.path.normpath(os.path.join(docs_root_path, os.path.basename(original_path)))

            if os.path.exists(candidate_in_destination) or not os.path.exists(candidate_in_root):
                return match.group(0)

            rewritten_path = self._to_markdown_path(
                os.path.relpath(candidate_in_root, start=destination_dir)
            )
            return f"{match.group(1)}{rewritten_path}{match.group(3)}"

        updated_content = image_pattern.sub(replace_match, content)

        with open(destination_path, "w", encoding="utf-8") as md_file:
            md_file.write(updated_content)

    def clear_package_docs(self,
                           package_name: str,
                           docs_path: str):

        """
        Remove package-specific docs from docs_path before rebuilding docs.
        """

        if not docs_path or not os.path.exists(docs_path):
            return

        for entry in os.listdir(docs_path):
            entry_path = os.path.join(docs_path, entry)

            if entry == f"{package_name}.md":
                if os.path.isfile(entry_path):
                    os.remove(entry_path)
                continue

            # Clean only package-prefixed documentation trees/files.
            if not entry.startswith(f"{package_name}-"):
                # Also clean notebook-derived images written at docs root.
                if self._is_notebook_generated_png(entry, package_name):
                    os.remove(entry_path)
                continue

            if os.path.isdir(entry_path):
                for root, _, files in os.walk(entry_path):
                    for file_name in files:
                        should_remove = (
                            file_name.endswith(".md")
                            or self._is_notebook_generated_png(file_name, package_name)
                        )
                        if should_remove:
                            os.remove(os.path.join(root, file_name))

                self._remove_empty_dirs(entry_path)
            else:
                should_remove = (
                    entry.endswith(".md")
                    or self._is_notebook_generated_png(entry, package_name)
                )
                if should_remove:
                    os.remove(entry_path)

    def _is_notebook_generated_png(self, filename: str, package_name: str) -> bool:

        """
        Recognize notebook-generated png files while leaving drawio png files untouched.
        """

        is_new_pattern = filename.startswith(f"{package_name}_ipynb_cell") and filename.endswith(".png")
        is_legacy_pattern = filename.startswith(f"{package_name}_cell") and "_out" in filename and filename.endswith(".png")
        return is_new_pattern or is_legacy_pattern

    def _remove_empty_dirs(self, directory_path: str):

        """
        Remove empty directories recursively.
        """

        if not os.path.isdir(directory_path):
            return

        for item_name in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item_name)
            if os.path.isdir(item_path):
                self._remove_empty_dirs(item_path)

        if not os.listdir(directory_path):
            os.rmdir(directory_path)
