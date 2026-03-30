from python_modules.components.paa_deps.setup_dir_handler import SetupDirHandler


def test_setup_dir_handler_copies_module(tmp_path):
    module_file = tmp_path / "mod.py"
    module_file.write_text("x = 1\n", encoding="utf-8")

    setup_dir = tmp_path / "setup"
    handler = SetupDirHandler(module_filepath=str(module_file), module_name="mod", setup_directory=str(setup_dir))
    handler.flush_n_make_setup_dir()
    handler.copy_module_to_setup_dir()

    assert (setup_dir / "mod.py").exists()


def test_setup_dir_handler_writes_readable_pyproject(tmp_path):
    module_file = tmp_path / "mod.py"
    module_file.write_text("x = 1\n", encoding="utf-8")
    pyproject_dir = tmp_path / "pyproject"

    handler = SetupDirHandler(
        module_filepath=str(module_file),
        module_name="mod",
        pyproject_directory=str(pyproject_dir),
        version="1.2.3",
        metadata={
            "name": "mod",
            "description": "desc",
            "author": "A",
            "author_email": "a@example.com",
            "project_urls": {"Source Repo": "https://example.com/repo"},
            "keywords": ["zeta", "alpha"],
        },
        requirements=["e_pkg>=1.0", "d_pkg>=1.0", "c_pkg>=1.0", "b_pkg>=1.0", "a_pkg>=1.0"],
        classifiers=["Topic :: Software Development", "Development Status :: 4 - Beta"],
    )

    handler.write_pyproject_file()

    pyproject_path = pyproject_dir / "mod.toml"
    content = pyproject_path.read_text(encoding="utf-8")

    assert "dependencies = [\n" in content
    assert content.index('"a_pkg>=1.0"') < content.index('"b_pkg>=1.0"')
    assert '"Source Repo" = "https://example.com/repo"' in content
