from pathlib import Path

import yaml

from python_modules.package_auto_assembler import PackageAutoAssembler
from python_modules.components.paa_deps.local_dependencies_handler import LocalDependaciesHandler
from python_modules.components.paa_deps.long_doc_handler import LongDocHandler
from python_modules.components.paa_deps.mkdocs_handler import MkDocsHandler
from python_modules.components.paa_deps.ppr_handler import PprHandler


def test_local_dependencies_handler_multiline_imports_are_handled(tmp_path):
    main_module = tmp_path / "main.py"
    deps_dir = tmp_path / "deps"
    deps_dir.mkdir()
    main_module.write_text("x = 1\n", encoding="utf-8")

    ldh = LocalDependaciesHandler(
        main_module_filepath=str(main_module),
        dependencies_dir=str(deps_dir),
    )

    module_content = (
        "import os\n"
        "from pkg import (\n"
        "    a,\n"
        "    b,\n"
        ")\n\n"
        "def f():\n"
        "    import pkg_resources\n"
        "    return 1\n"
    )

    imports = ldh._extract_imports(module_content)
    assert "import os" in imports
    assert "from pkg import (\n    a,\n    b,\n)" in imports
    assert not any("pkg_resources" in imp for imp in imports)

    cleaned = ldh._remove_imports(module_content)
    assert "import os" not in cleaned
    assert "from pkg import" not in cleaned
    assert "import pkg_resources" in cleaned


def test_clear_package_docs_keeps_drawio_png_and_other_packages(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "mypkg.md").write_text("desc", encoding="utf-8")
    (docs_dir / "mypkg-extra.md").write_text("x", encoding="utf-8")
    (docs_dir / "mypkg_ipynb_cell1_out1.png").write_bytes(b"a")
    (docs_dir / "mypkg_cell1_out1.png").write_bytes(b"legacy")
    (docs_dir / "mypkg-drawio.png").write_bytes(b"drawio")

    package_subdir = docs_dir / "mypkg-guides"
    package_subdir.mkdir()
    (package_subdir / "guide.md").write_text("guide", encoding="utf-8")
    (package_subdir / "mypkg_ipynb_cell2_out1.png").write_bytes(b"a")
    (package_subdir / "diagram.png").write_bytes(b"drawio")

    (docs_dir / "otherpkg.md").write_text("other", encoding="utf-8")

    ldh = LongDocHandler(module_name="mypkg")
    ldh.clear_package_docs(package_name="mypkg", docs_path=str(docs_dir))

    assert not (docs_dir / "mypkg.md").exists()
    assert not (docs_dir / "mypkg-extra.md").exists()
    assert not (docs_dir / "mypkg_ipynb_cell1_out1.png").exists()
    assert not (docs_dir / "mypkg_cell1_out1.png").exists()
    assert (docs_dir / "mypkg-drawio.png").exists()

    assert not (package_subdir / "guide.md").exists()
    assert not (package_subdir / "mypkg_ipynb_cell2_out1.png").exists()
    assert (package_subdir / "diagram.png").exists()

    assert (docs_dir / "otherpkg.md").exists()


def test_mkdocs_nav_skips_empty_markdown(tmp_path):
    project = tmp_path / "mkdocs_proj"
    docs = project / "docs"
    docs.mkdir(parents=True)

    (docs / "index.md").write_text("intro", encoding="utf-8")
    (docs / "good.md").write_text("content", encoding="utf-8")
    (docs / "empty.md").write_text(" \n\t", encoding="utf-8")

    sub = docs / "guides"
    sub.mkdir()
    (sub / "a.md").write_text("", encoding="utf-8")
    (sub / "b.md").write_text("hello", encoding="utf-8")

    mkh = MkDocsHandler(
        package_name="mypkg",
        docs_file_paths={},
        project_name=str(project),
    )

    nav = mkh._generate_nav_entries(str(docs))
    assert "Good: good.md" in nav
    assert "Empty: empty.md" not in nav
    assert "Guides:" in nav
    assert "B: b.md" in nav
    assert "A: a.md" not in nav


def test_make_mkdocs_site_resolves_nested_extra_docs_image_paths(tmp_path, monkeypatch):
    docs_dir = tmp_path / ".paa" / "docs"
    nested_dir = docs_dir / "mypkg-guides"
    nested_dir.mkdir(parents=True)

    image_path = docs_dir / "mypkg_ipynb_cell12_out0.png"
    image_path.write_bytes(b"png")
    (nested_dir / "benchmark_25_example_functions.md").write_text(
        "![plot](../mypkg_ipynb_cell12_out0.png)\n",
        encoding="utf-8",
    )

    captured = {}

    class FakeMkDocsHandler:
        def __init__(self, **kwargs):
            captured["docs_file_paths"] = dict(kwargs["docs_file_paths"])
            captured["project_name"] = kwargs["project_name"]

        def create_mkdocs_dir(self):
            pass

        def move_files_to_docs(self, image_path_replacements=None):
            captured["image_path_replacements"] = dict(image_path_replacements or {})

        def generate_markdown_for_images(self):
            pass

        def create_index(self):
            pass

        def create_mkdocs_yml(self):
            pass

        def build_mkdocs_site(self):
            pass

    paa = PackageAutoAssembler(
        module_name="mypkg",
        module_filepath=str(tmp_path / "python_modules" / "mypkg.py"),
        docs_path=str(docs_dir),
        setup_directory=str(tmp_path / "pkg"),
        add_mkdocs_site=True,
        mkdocs_class=FakeMkDocsHandler,
    )

    (tmp_path / "python_modules").mkdir()
    (tmp_path / "python_modules" / "mypkg.py").write_text('"""Docstring."""\n', encoding="utf-8")

    monkeypatch.setattr(LongDocHandler, "get_pypi_badge", lambda self, module_name: "")

    paa.make_mkdocs_site()

    assert str(image_path) in captured["docs_file_paths"]
    assert captured["docs_file_paths"][str(image_path)] == "images/mypkg_ipynb_cell12_out0.png"
    assert captured["image_path_replacements"]["../mypkg_ipynb_cell12_out0.png"] == "images/mypkg_ipynb_cell12_out0.png"


def test_make_mkdocs_site_marks_top_level_markdown_images_as_referenced(tmp_path, monkeypatch):
    docs_dir = tmp_path / ".paa" / "docs"
    docs_dir.mkdir(parents=True)

    image_path = docs_dir / "mypkg-usage.png"
    image_path.write_bytes(b"png")
    (docs_dir / "mypkg-guide.md").write_text(
        "![plot](mypkg-usage.png)\n",
        encoding="utf-8",
    )

    captured = {}

    class FakeMkDocsHandler:
        def __init__(self, **kwargs):
            captured["docs_file_paths"] = dict(kwargs["docs_file_paths"])
            captured["referenced_image_names"] = set(kwargs["referenced_image_names"])

        def create_mkdocs_dir(self):
            pass

        def move_files_to_docs(self, image_path_replacements=None):
            captured["image_path_replacements"] = dict(image_path_replacements or {})

        def generate_markdown_for_images(self):
            pass

        def create_index(self):
            pass

        def create_mkdocs_yml(self):
            pass

        def build_mkdocs_site(self):
            pass

    paa = PackageAutoAssembler(
        module_name="mypkg",
        module_filepath=str(tmp_path / "python_modules" / "mypkg.py"),
        docs_path=str(docs_dir),
        setup_directory=str(tmp_path / "pkg"),
        add_mkdocs_site=True,
        mkdocs_class=FakeMkDocsHandler,
    )

    (tmp_path / "python_modules").mkdir()
    (tmp_path / "python_modules" / "mypkg.py").write_text('"""Docstring."""\n', encoding="utf-8")

    monkeypatch.setattr(LongDocHandler, "get_pypi_badge", lambda self, module_name: "")

    paa.make_mkdocs_site()

    assert str(image_path) in captured["docs_file_paths"]
    assert captured["docs_file_paths"][str(image_path)] == "images/mypkg-usage.png"
    assert captured["image_path_replacements"]["mypkg-usage.png"] == "images/mypkg-usage.png"
    assert "mypkg-usage.png" in captured["referenced_image_names"]


def test_make_mkdocs_site_ignores_non_prefixed_package_name_collisions(tmp_path, monkeypatch):
    docs_dir = tmp_path / ".paa" / "docs"
    docs_dir.mkdir(parents=True)

    own_doc = docs_dir / "pkg_alpha.md"
    own_doc.write_text("primary docs\n", encoding="utf-8")
    colliding_doc = docs_dir / "pkg_alpha_extra.md"
    colliding_doc.write_text("should stay out\n", encoding="utf-8")

    captured = {}

    class FakeMkDocsHandler:
        def __init__(self, **kwargs):
            captured["docs_file_paths"] = dict(kwargs["docs_file_paths"])

        def create_mkdocs_dir(self):
            pass

        def move_files_to_docs(self, image_path_replacements=None):
            pass

        def generate_markdown_for_images(self):
            pass

        def create_index(self):
            pass

        def create_mkdocs_yml(self):
            pass

        def build_mkdocs_site(self):
            pass

    paa = PackageAutoAssembler(
        module_name="pkg_alpha",
        module_filepath=str(tmp_path / "python_modules" / "pkg_alpha.py"),
        docs_path=str(docs_dir),
        setup_directory=str(tmp_path / "pkg"),
        add_mkdocs_site=True,
        mkdocs_class=FakeMkDocsHandler,
    )

    (tmp_path / "python_modules").mkdir()
    (tmp_path / "python_modules" / "pkg_alpha.py").write_text('"""Docstring."""\n', encoding="utf-8")

    monkeypatch.setattr(LongDocHandler, "get_pypi_badge", lambda self, module_name: "")

    paa.make_mkdocs_site()

    docs_file_paths = captured["docs_file_paths"]
    assert str(own_doc) in docs_file_paths
    assert docs_file_paths[str(own_doc)] == "description.md"
    assert str(colliding_doc) not in docs_file_paths


def test_unfold_package_restores_pyproject_to_dot_paa(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    package_name = "pkg_alpha"
    package_path = tmp_path / "fake_pkg"
    tracking = package_path / ".paa.tracking"
    tracking.mkdir(parents=True)

    (tracking / "pyproject.toml").write_text("[project]\nname='pkg-alpha'\n", encoding="utf-8")
    (tracking / ".paa.config").write_text(
        yaml.safe_dump(
            {
                "module_dir": None,
                "dependencies_dir": None,
                "cli_dir": None,
                "api_routes_dir": None,
                "streamlit_dir": None,
                "example_notebooks_path": None,
                "drawio_dir": None,
                "tests_dir": None,
                "artifacts_dir": None,
                "extra_docs_dir": None,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    from python_modules.components.paa_deps import ppr_handler as ppr_module

    monkeypatch.setattr(ppr_module.pkg_resources, "files", lambda _: package_path)

    ppr = PprHandler()
    status = ppr.unfold_package(module_name=package_name)

    assert status is None
    restored = tmp_path / ".paa" / "pyproject" / f"{package_name}.toml"
    assert restored.exists()
    assert "pkg-alpha" in restored.read_text(encoding="utf-8")


def test_remove_package_removes_only_tracked_components(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    deps_dir = tmp_path / "python_modules" / "components"
    deps_dir.mkdir(parents=True)
    (deps_dir / "comp_a.py").write_text("A = 1\n", encoding="utf-8")
    (deps_dir / "comp_b.py").write_text("B = 1\n", encoding="utf-8")

    (tmp_path / ".paa.config").write_text(
        yaml.safe_dump(
            {
                "module_dir": str(tmp_path / "python_modules"),
                "dependencies_dir": str(deps_dir),
                "cli_dir": None,
                "api_routes_dir": None,
                "streamlit_dir": None,
                "example_notebooks_path": None,
                "drawio_dir": None,
                "tests_dir": None,
                "artifacts_dir": None,
                "extra_docs_dir": None,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    package_name = "pkg_alpha"
    package_path = tmp_path / "fake_pkg"
    tracked_components = package_path / ".paa.tracking" / "python_modules" / "components"
    tracked_components.mkdir(parents=True)
    (tracked_components / "comp_a.py").write_text("A = 1\n", encoding="utf-8")

    from python_modules.components.paa_deps import ppr_handler as ppr_module

    monkeypatch.setattr(ppr_module.pkg_resources, "files", lambda _: package_path)

    ppr = PprHandler()
    ppr.remove_package(module_name=package_name)

    assert not (deps_dir / "comp_a.py").exists()
    assert (deps_dir / "comp_b.py").exists()


def test_remove_package_preserves_component_used_by_other_module(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    module_dir = tmp_path / "python_modules"
    deps_dir = module_dir / "components"
    deps_dir.mkdir(parents=True)
    (deps_dir / "shared_dep.py").write_text("SHARED = 1\n", encoding="utf-8")
    (deps_dir / "only_alpha.py").write_text("ALPHA = 1\n", encoding="utf-8")

    (module_dir / "pkg_alpha.py").write_text("x = 1\n", encoding="utf-8")
    (module_dir / "pkg_beta.py").write_text(
        "from components import shared_dep\n",
        encoding="utf-8",
    )

    (tmp_path / ".paa.config").write_text(
        yaml.safe_dump(
            {
                "module_dir": str(module_dir),
                "dependencies_dir": str(deps_dir),
                "cli_dir": None,
                "api_routes_dir": None,
                "streamlit_dir": None,
                "example_notebooks_path": None,
                "drawio_dir": None,
                "tests_dir": None,
                "artifacts_dir": None,
                "extra_docs_dir": None,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    package_name = "pkg_alpha"
    package_path = tmp_path / "fake_pkg"
    tracked_components = package_path / ".paa.tracking" / "python_modules" / "components"
    tracked_components.mkdir(parents=True)
    (tracked_components / "shared_dep.py").write_text("SHARED = 1\n", encoding="utf-8")
    (tracked_components / "only_alpha.py").write_text("ALPHA = 1\n", encoding="utf-8")

    from python_modules.components.paa_deps import ppr_handler as ppr_module

    monkeypatch.setattr(ppr_module.pkg_resources, "files", lambda _: package_path)

    ppr = PprHandler()
    ppr.remove_package(module_name=package_name)

    assert (deps_dir / "shared_dep.py").exists()
    assert not (deps_dir / "only_alpha.py").exists()


def test_unfold_package_ignores_null_repo_config_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    package_name = "pkg_alpha"
    package_path = tmp_path / "fake_pkg"
    tracking = package_path / ".paa.tracking"
    tracked_extra_docs = tracking / "extra_docs"
    tracked_extra_docs.mkdir(parents=True)
    (tracked_extra_docs / "guide.md").write_text("hello", encoding="utf-8")

    (tracking / ".paa.config").write_text(
        yaml.safe_dump(
            {
                "module_dir": "python_modules",
                "dependencies_dir": "python_modules/components",
                "cli_dir": "cli",
                "api_routes_dir": "api_routes",
                "streamlit_dir": "streamlit",
                "example_notebooks_path": "example_notebooks",
                "drawio_dir": "drawio",
                "tests_dir": "tests",
                "artifacts_dir": "artifacts",
                "extra_docs_dir": "extra_docs",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    (tmp_path / ".paa.config").write_text(
        yaml.safe_dump(
            {
                "module_dir": "python_modules",
                "dependencies_dir": "python_modules/components",
                "cli_dir": None,
                "api_routes_dir": None,
                "streamlit_dir": None,
                "example_notebooks_path": None,
                "drawio_dir": None,
                "tests_dir": None,
                "artifacts_dir": None,
                "extra_docs_dir": None,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    from python_modules.components.paa_deps import ppr_handler as ppr_module

    monkeypatch.setattr(ppr_module.pkg_resources, "files", lambda _: package_path)

    ppr = PprHandler()
    ppr.unfold_package(module_name=package_name)

    assert (tmp_path / "extra_docs" / package_name / "guide.md").exists()


def test_unfold_package_restores_skills_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    package_name = "pkg_alpha"
    package_path = tmp_path / "fake_pkg"
    tracking = package_path / ".paa.tracking"
    tracked_skills = tracking / "skills"
    tracked_skills.mkdir(parents=True)
    (tracked_skills / "s1").mkdir()
    (tracked_skills / "s1" / "SKILL.md").write_text("# skill\n", encoding="utf-8")

    (tracking / ".paa.config").write_text(
        yaml.safe_dump(
            {
                "module_dir": None,
                "dependencies_dir": None,
                "cli_dir": None,
                "api_routes_dir": None,
                "streamlit_dir": None,
                "example_notebooks_path": None,
                "drawio_dir": None,
                "tests_dir": None,
                "artifacts_dir": None,
                "extra_docs_dir": None,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    from python_modules.components.paa_deps import ppr_handler as ppr_module

    monkeypatch.setattr(ppr_module.pkg_resources, "files", lambda _: package_path)

    ppr = PprHandler()
    ppr.unfold_package(module_name=package_name)

    assert (tmp_path / "skills" / package_name / "s1" / "SKILL.md").exists()


def test_remove_package_removes_skills_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    skills_pkg_dir = tmp_path / "skills" / "pkg_alpha"
    skills_pkg_dir.mkdir(parents=True)
    (skills_pkg_dir / "s1").mkdir()
    (skills_pkg_dir / "s1" / "SKILL.md").write_text("# skill\n", encoding="utf-8")

    (tmp_path / ".paa.config").write_text(
        yaml.safe_dump(
            {
                "module_dir": None,
                "dependencies_dir": None,
                "cli_dir": None,
                "api_routes_dir": None,
                "streamlit_dir": None,
                "example_notebooks_path": None,
                "drawio_dir": None,
                "tests_dir": None,
                "artifacts_dir": None,
                "extra_docs_dir": None,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    ppr = PprHandler()
    ppr.remove_package(module_name="pkg_alpha")

    assert not skills_pkg_dir.exists()


def test_rename_package_renames_skills_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    skills_old_dir = tmp_path / "skills" / "pkg_alpha"
    skills_old_dir.mkdir(parents=True)
    (skills_old_dir / "s1").mkdir()
    (skills_old_dir / "s1" / "SKILL.md").write_text("# skill\n", encoding="utf-8")

    (tmp_path / ".paa.config").write_text(
        yaml.safe_dump(
            {
                "module_dir": None,
                "dependencies_dir": None,
                "cli_dir": None,
                "api_routes_dir": None,
                "streamlit_dir": None,
                "example_notebooks_path": None,
                "drawio_dir": None,
                "tests_dir": None,
                "artifacts_dir": None,
                "extra_docs_dir": None,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    ppr = PprHandler()
    ppr.rename_package(module_name="pkg_alpha", new_module_name="pkg_beta")

    assert not skills_old_dir.exists()
    assert (tmp_path / "skills" / "pkg_beta" / "s1" / "SKILL.md").exists()
