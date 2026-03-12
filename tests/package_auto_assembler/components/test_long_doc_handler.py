import nbformat
import json
from pathlib import Path

from python_modules.components.paa_deps.long_doc_handler import LongDocHandler


def test_long_doc_handler_clear_package_docs(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "mypkg_ipynb_cell1_out1.png").write_bytes(b"x")

    handler = LongDocHandler(module_name="mypkg")
    handler.clear_package_docs("mypkg", str(docs_dir))

    assert not (docs_dir / "mypkg_ipynb_cell1_out1.png").exists()


def test_long_doc_handler_hides_tagged_code_cells_in_markdown(tmp_path):
    notebook_path = tmp_path / "demo.ipynb"
    md_path = tmp_path / "demo.md"

    nb = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell("#| paa-hide-code\nsecret_value = 123"),
            nbformat.v4.new_code_cell("visible_value = 456"),
        ]
    )
    with open(notebook_path, "w", encoding="utf-8") as fh:
        nbformat.write(nb, fh)

    handler = LongDocHandler(module_name="demo")
    handler.convert_notebook_to_md(str(notebook_path), str(md_path))

    rendered = md_path.read_text(encoding="utf-8")
    assert "secret_value = 123" not in rendered
    assert "visible_value = 456" in rendered


def test_long_doc_handler_drops_tagged_cell_without_output(tmp_path):
    notebook_path = tmp_path / "demo_no_output.ipynb"
    md_path = tmp_path / "demo_no_output.md"

    nb = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell("#| paa-hide-code\nhidden_no_output = 1"),
            nbformat.v4.new_markdown_cell("after"),
        ]
    )
    with open(notebook_path, "w", encoding="utf-8") as fh:
        nbformat.write(nb, fh)

    handler = LongDocHandler(module_name="demo")
    handler.convert_notebook_to_md(str(notebook_path), str(md_path))

    rendered = md_path.read_text(encoding="utf-8")
    assert "hidden_no_output = 1" not in rendered
    assert "after" in rendered


def test_long_doc_handler_hides_tagged_code_but_keeps_output_when_executed(tmp_path, monkeypatch):
    notebook_path = tmp_path / "demo_exec.ipynb"
    md_path = tmp_path / "demo_exec.md"

    nb = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell("#| paa-hide-code\nprint('HIDDEN_OUTPUT')"),
            nbformat.v4.new_code_cell("print('VISIBLE_OUTPUT')"),
        ]
    )
    nb.cells[0]["outputs"] = [nbformat.v4.new_output("stream", name="stdout", text="HIDDEN_OUTPUT\n")]
    nb.cells[1]["outputs"] = [nbformat.v4.new_output("stream", name="stdout", text="VISIBLE_OUTPUT\n")]
    nb.cells[0]["execution_count"] = 1
    nb.cells[1]["execution_count"] = 2
    with open(notebook_path, "w", encoding="utf-8") as fh:
        nbformat.write(nb, fh)

    monkeypatch.setattr(
        "python_modules.components.paa_deps.long_doc_handler.ExecutePreprocessor.preprocess",
        lambda self, notebook_node, resources: (notebook_node, resources),
    )

    handler = LongDocHandler(module_name="demo", kernel_name="python")
    handler.convert_and_execute_notebook_to_md(str(notebook_path), str(md_path), timeout=120)

    rendered = md_path.read_text(encoding="utf-8")
    assert "print('HIDDEN_OUTPUT')" not in rendered
    assert "HIDDEN_OUTPUT" in rendered
    assert "VISIBLE_OUTPUT" in rendered


def test_long_doc_handler_accepts_notebook_cells_with_id_field(tmp_path):
    notebook_path = tmp_path / "with_ids.ipynb"
    md_path = tmp_path / "with_ids.md"

    notebook_data = {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "abc123",
                "metadata": {},
                "source": "# Title",
            },
            {
                "cell_type": "code",
                "id": "def456",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": "x = 1",
            },
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    notebook_path.write_text(json.dumps(notebook_data), encoding="utf-8")

    handler = LongDocHandler(module_name="demo")
    handler.convert_notebook_to_md(str(notebook_path), str(md_path))

    rendered = md_path.read_text(encoding="utf-8")
    assert "Title" in rendered


def test_prep_extra_docs_keeps_notebook_plot_images_in_docs_root(tmp_path):
    extra_docs_dir = tmp_path / "extra_docs" / "mypkg" / "subfolder"
    extra_docs_dir.mkdir(parents=True)
    docs_dir = tmp_path / ".paa" / "docs"

    notebook_path = extra_docs_dir / "myfile.ipynb"
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell("print('plot')"),
        ]
    )
    notebook.cells[0]["outputs"] = [
        nbformat.v4.new_output(
            "display_data",
            data={"image/png": "YQ=="},
            metadata={},
        )
    ]
    notebook.cells[0]["execution_count"] = 1
    notebook_path.write_text(nbformat.writes(notebook), encoding="utf-8")

    handler = LongDocHandler(module_name="mypkg")
    handler.prep_extra_docs(
        package_name="mypkg",
        extra_docs_dir=str(tmp_path / "extra_docs" / "mypkg"),
        docs_path=str(docs_dir),
    )

    markdown_path = docs_dir / "mypkg-subfolder" / "myfile.md"
    image_path = docs_dir / "mypkg_ipynb_cell0_out0.png"

    assert markdown_path.exists()
    assert image_path.exists()
    assert not (docs_dir / "mypkg-subfolder" / "mypkg_ipynb_cell0_out0.png").exists()

    rendered = markdown_path.read_text(encoding="utf-8")
    expected_ref = f"../{image_path.name}"
    assert str(expected_ref) in rendered


def test_prep_extra_docs_rewrites_nested_markdown_refs_to_root_images(tmp_path):
    extra_docs_dir = tmp_path / "extra_docs" / "mypkg" / "concepts"
    extra_docs_dir.mkdir(parents=True)
    docs_dir = tmp_path / ".paa" / "docs"
    docs_dir.mkdir(parents=True)

    (docs_dir / "mypkg-usage.png").write_bytes(b"png")
    (extra_docs_dir / "guide.md").write_text(
        "![plot](mypkg-usage.png)\n",
        encoding="utf-8",
    )

    handler = LongDocHandler(module_name="mypkg")
    handler.prep_extra_docs(
        package_name="mypkg",
        extra_docs_dir=str(tmp_path / "extra_docs" / "mypkg"),
        docs_path=str(docs_dir),
    )

    rendered = (docs_dir / "mypkg-concepts" / "guide.md").read_text(encoding="utf-8")
    assert "../mypkg-usage.png" in rendered
