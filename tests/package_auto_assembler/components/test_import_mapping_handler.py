from python_modules.components.paa_deps.import_mapping_handler import ImportMappingHandler


def test_import_mapping_handler_loads_mapping(tmp_path):
    mapping_file = tmp_path / "mapping.json"
    base_mapping_file = tmp_path / "base_mapping.json"
    mapping_file.write_text('{"x": "override", "z": "w"}', encoding="utf-8")
    base_mapping_file.write_text('{"x": "y", "a": "b"}', encoding="utf-8")

    handler = ImportMappingHandler(mapping_filepath=str(mapping_file))
    mappings = handler.load_package_mappings(base_mapping_filepath=str(base_mapping_file))
    assert mappings.get("x") == "override"
    assert mappings.get("a") == "b"
    assert mappings.get("z") == "w"
