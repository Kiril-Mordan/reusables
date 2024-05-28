import os
import sys
from package_auto_assembler import LongDocHandler, MkDocsHandler



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