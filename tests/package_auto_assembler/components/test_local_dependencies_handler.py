from python_modules.components.paa_deps.local_dependencies_handler import LocalDependaciesHandler


def test_local_dependencies_handler_paths_include_referenced_deps(tmp_path):
    main_module = tmp_path / "main.py"
    deps_dir = tmp_path / "deps"
    deps_dir.mkdir()
    (deps_dir / "dep_a.py").write_text("def dep_a():\n    return 1\n", encoding="utf-8")
    main_module.write_text("from dep_a import dep_a\n", encoding="utf-8")

    handler = LocalDependaciesHandler(main_module_filepath=str(main_module), dependencies_dir=str(deps_dir))
    file_paths = handler.get_module_deps_path()
    assert str(main_module) in file_paths
    assert str(deps_dir / "dep_a") in file_paths


def test_local_dependencies_handler_extract_imports_keeps_function_local_imports():
    content = "\n".join(
        [
            "from aa import (",
            "    bb,",
            "    cc,",
            ")",
            "",
            "def f():",
            "    import inner_mod",
            "    return inner_mod",
        ]
    )

    handler = LocalDependaciesHandler(main_module_filepath="main.py", dependencies_dir="deps")
    imports = handler._extract_imports(content)
    stripped = handler._remove_imports(content)

    assert imports == ["from aa import (\n    bb,\n    cc,\n)"]
    assert "import inner_mod" in stripped
    assert "from aa import" not in stripped


def test_local_dependencies_handler_rejects_selected_component_cross_imports(tmp_path):
    main_module = tmp_path / "main.py"
    deps_dir = tmp_path / "deps"
    deps_dir.mkdir()

    (deps_dir / "dep_a.py").write_text(
        "from dep_b import helper\n\n"
        "def dep_a():\n"
        "    return helper()\n",
        encoding="utf-8",
    )
    (deps_dir / "dep_b.py").write_text(
        "def helper():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    main_module.write_text(
        "from dep_a import dep_a\n",
        encoding="utf-8",
    )

    handler = LocalDependaciesHandler(
        main_module_filepath=str(main_module),
        dependencies_dir=str(deps_dir),
    )

    try:
        handler.combine_modules()
        assert False, "Expected cross-component import validation to fail"
    except ValueError as exc:
        assert "Selected components must not import local components directly" in str(exc)


def test_local_dependencies_handler_rejects_dotted_component_path_import(tmp_path):
    main_module = tmp_path / "main.py"
    deps_dir = tmp_path / "python_modules" / "component" / "paa_deps"
    deps_dir.mkdir(parents=True)

    (deps_dir / "dep_a.py").write_text(
        "from python_modules.component.paa_deps.dep_b import helper\n\n"
        "def dep_a():\n"
        "    return helper()\n",
        encoding="utf-8",
    )
    (deps_dir / "dep_b.py").write_text(
        "def helper():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    main_module.write_text("from dep_a import dep_a\n", encoding="utf-8")

    handler = LocalDependaciesHandler(
        main_module_filepath=str(main_module),
        dependencies_dir=str(deps_dir),
    )

    try:
        handler.combine_modules()
        assert False, "Expected dotted local-component import validation to fail"
    except ValueError as exc:
        assert "Selected components must not import local components directly" in str(exc)
