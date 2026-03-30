from python_modules.components.paa_deps.metadata_handler import MetadataHandler


def test_metadata_handler_detects_metadata(tmp_path):
    module_file = tmp_path / "mod.py"
    module_file.write_text("__package_metadata__ = {'name': 'mod'}\n", encoding="utf-8")

    handler = MetadataHandler(module_filepath=str(module_file))
    assert handler.is_metadata_available() is True


def test_metadata_handler_extracts_metadata_and_adds_keyword(tmp_path):
    module_file = tmp_path / "mod.py"
    module_file.write_text(
        "\n".join(
            [
                "__package_metadata__ = {",
                "    'name': 'mod',",
                "    'version': '0.1.0'",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    handler = MetadataHandler(module_filepath=str(module_file))
    metadata = handler.get_package_metadata()

    assert metadata["name"] == "mod"
    assert metadata["version"] == "0.1.0"
    assert "aa-paa-tool" in metadata["keywords"]
