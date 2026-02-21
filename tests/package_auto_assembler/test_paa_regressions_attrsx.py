from pathlib import Path

from python_modules.package_auto_assembler import PackageAutoAssembler
from python_modules.components.paa_deps.local_dependencies_handler import LocalDependaciesHandler


def test_package_auto_assembler_post_init_initializes_attrsx_handlers(tmp_path):
    module_file = tmp_path / "mod.py"
    module_file.write_text("__package_metadata__ = {'name': 'mod'}\n", encoding="utf-8")

    paa = PackageAutoAssembler(
        module_name="mod",
        module_filepath=str(module_file),
    )

    assert paa.metadata_h is not None
    assert paa.import_mapping_h is not None
    assert isinstance(paa.metadata_h, paa.metadata_class)
    assert isinstance(paa.import_mapping_h, paa.import_mapping_class)
    assert paa.metadata_h.module_filepath == str(module_file)


def test_combine_modules_does_not_hoist_function_local_imports(tmp_path):
    deps_dir = tmp_path / "components"
    deps_dir.mkdir()

    dep_module = deps_dir / "dep1.py"
    dep_module.write_text(
        "import os\n\n"
        "def helper():\n"
        "    import pkg_resources\n"
        "    return os.getcwd()\n",
        encoding="utf-8",
    )

    main_module = tmp_path / "main.py"
    main_module.write_text(
        "__package_metadata__ = {'name': 'main'}\n\n"
        "from dep1 import helper\n\n"
        "def run():\n"
        "    return helper()\n",
        encoding="utf-8",
    )

    ldh = LocalDependaciesHandler(
        main_module_filepath=str(main_module),
        dependencies_dir=str(deps_dir),
    )
    combined = ldh.combine_modules()

    # module-level dependency import is preserved
    assert "import os" in combined
    # function-local import should remain in function body, not hoisted to top imports list
    assert "\ndef helper():\n    import pkg_resources\n" in combined
    # guard against exact top-level hoist pattern
    assert "\nimport pkg_resources\n\ndef helper():" not in combined


def test_cli_no_removed_ppr_initializer_usage():
    cli_path = Path("cli/package_auto_assembler.py")
    content = cli_path.read_text(encoding="utf-8")
    assert "_initialize_ppr_handler(" not in content
