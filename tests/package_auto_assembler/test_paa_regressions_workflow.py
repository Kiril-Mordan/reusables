import os
from pathlib import Path

from python_modules.package_auto_assembler import PackageAutoAssembler
from python_modules.components.paa_deps.ppr_handler import PprHandler


class _DummyDrawioHandler:
    def __init__(self, **kwargs):
        pass

    def prepare_drawio(self):
        return None


class _DummyArtifactsHandler:
    def __init__(self, **kwargs):
        self.artifacts_filepaths = {}
        self.last_manifest_input = None

    def load_additional_artifacts(self):
        return {}

    def make_manifest(self, artifacts_filepaths):
        self.last_manifest_input = dict(artifacts_filepaths)
        self.artifacts_filepaths = dict(artifacts_filepaths)


def test_prepare_artifacts_tracks_pyproject_file(tmp_path):
    module_file = tmp_path / "m.py"
    module_file.write_text("__package_metadata__ = {'name':'m'}\n", encoding="utf-8")

    pyproject_dir = tmp_path / ".paa" / "pyproject"
    pyproject_dir.mkdir(parents=True)
    pyproject_file = pyproject_dir / "m.toml"
    pyproject_file.write_text("[project]\nname='m'\n", encoding="utf-8")

    paa = PackageAutoAssembler(
        module_name="m",
        module_filepath=str(module_file),
        pyproject_dir=str(pyproject_dir),
        add_artifacts=True,
        drawio_class=_DummyDrawioHandler,
        artifacts_class=_DummyArtifactsHandler,
    )

    paa.prepare_artifacts(artifacts_filepaths={})

    assert ".paa.tracking/pyproject.toml" in paa.artifacts_h.last_manifest_input
    assert (
        paa.artifacts_h.last_manifest_input[".paa.tracking/pyproject.toml"]
        == str(pyproject_file)
    )


def test_prepare_artifacts_tracks_license_and_notice_files(tmp_path):
    module_file = tmp_path / "m.py"
    module_file.write_text("__package_metadata__ = {'name':'m'}\n", encoding="utf-8")

    license_file = tmp_path / "LICENSE"
    notice_file = tmp_path / "NOTICE"
    license_file.write_text("license", encoding="utf-8")
    notice_file.write_text("notice", encoding="utf-8")

    paa = PackageAutoAssembler(
        module_name="m",
        module_filepath=str(module_file),
        license_path=str(license_file),
        notice_path=str(notice_file),
        add_artifacts=True,
        drawio_class=_DummyDrawioHandler,
        artifacts_class=_DummyArtifactsHandler,
    )

    paa.prepare_artifacts(artifacts_filepaths={})

    assert paa.artifacts_h.last_manifest_input[".paa.tracking/LICENSE"] == str(license_file)
    assert paa.artifacts_h.last_manifest_input[".paa.tracking/NOTICE"] == str(notice_file)


def test_unfold_package_restores_license_and_notice(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    package_name = "pkg_alpha"
    package_path = tmp_path / "fake_pkg"
    tracking = package_path / ".paa.tracking"
    tracking.mkdir(parents=True)

    (tracking / "LICENSE").write_text("L", encoding="utf-8")
    (tracking / "NOTICE").write_text("N", encoding="utf-8")
    (tracking / ".paa.config").write_text(
        "\n".join(
            [
                "module_dir: null",
                "dependencies_dir: null",
                "cli_dir: null",
                "api_routes_dir: null",
                "streamlit_dir: null",
                "example_notebooks_path: null",
                "drawio_dir: null",
                "tests_dir: null",
                "artifacts_dir: null",
                "extra_docs_dir: null",
                "licenses_dir: licenses",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    from python_modules.components.paa_deps import ppr_handler as ppr_module

    monkeypatch.setattr(ppr_module.pkg_resources, "files", lambda _: package_path)

    ppr = PprHandler()
    ppr.unfold_package(module_name=package_name)

    assert (tmp_path / "licenses" / package_name / "LICENSE").read_text(encoding="utf-8") == "L"
    assert (tmp_path / "licenses" / package_name / "NOTICE").read_text(encoding="utf-8") == "N"


def test_unfold_dirs_module_subdir_replaces_existing_content(tmp_path):
    package_path = tmp_path / "pkg"
    packaged_tests = package_path / "tests"
    packaged_tests.mkdir(parents=True)
    (packaged_tests / "new.txt").write_text("new", encoding="utf-8")

    repo_tests_root = tmp_path / "repo_tests"
    module_name = "sample_mod"
    target_module_dir = repo_tests_root / module_name
    target_module_dir.mkdir(parents=True)
    (target_module_dir / "old.txt").write_text("old", encoding="utf-8")

    ppr = PprHandler()
    ppr._unfold_dirs(
        repo_dir=str(repo_tests_root),
        dir_type="tests",
        packaged_name="tests",
        package_path=str(package_path),
        module_name_subdir=True,
        module_name=module_name,
    )

    assert not (target_module_dir / "old.txt").exists()
    assert (target_module_dir / "new.txt").exists()


def test_unfold_file_overwrites_existing_target_file(tmp_path):
    package_path = tmp_path / "pkg"
    tracking = package_path / ".paa.tracking" / "python_modules"
    tracking.mkdir(parents=True)
    (tracking / "mod.py").write_text("x=2\n", encoding="utf-8")

    repo_modules = tmp_path / "python_modules"
    repo_modules.mkdir()
    target_file = repo_modules / "mod.py"
    target_file.write_text("x=1\n", encoding="utf-8")

    ppr = PprHandler()
    ppr._unfold_file(
        repo_path=str(repo_modules),
        file_type="main_module",
        file_extension=".py",
        packaged_name=".paa.tracking/python_modules/mod.py",
        package_path=str(package_path),
        module_name="mod",
    )

    assert target_file.read_text(encoding="utf-8") == "x=2\n"


def test_remove_package_removes_license_and_notice_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    licenses_pkg_dir = tmp_path / "licenses" / "pkg_alpha"
    licenses_pkg_dir.mkdir(parents=True)
    (licenses_pkg_dir / "LICENSE").write_text("L", encoding="utf-8")
    (licenses_pkg_dir / "NOTICE").write_text("N", encoding="utf-8")

    (tmp_path / ".paa.config").write_text(
        "\n".join(
            [
                "module_dir: null",
                "dependencies_dir: null",
                "cli_dir: null",
                "api_routes_dir: null",
                "streamlit_dir: null",
                "example_notebooks_path: null",
                "drawio_dir: null",
                "tests_dir: null",
                "artifacts_dir: null",
                "extra_docs_dir: null",
                "licenses_dir: licenses",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    ppr = PprHandler()
    ppr.remove_package(module_name="pkg_alpha")

    assert not (licenses_pkg_dir / "LICENSE").exists()
    assert not (licenses_pkg_dir / "NOTICE").exists()
    assert not licenses_pkg_dir.exists()


def test_prepare_artifacts_tracks_skills_dir(tmp_path):
    module_name = "m"
    module_file = tmp_path / f"{module_name}.py"
    module_file.write_text("__package_metadata__ = {'name':'m'}\n", encoding="utf-8")

    skills_dir = tmp_path / "skills" / module_name
    skills_dir.mkdir(parents=True)
    (skills_dir / "sample_skill").mkdir()
    (skills_dir / "sample_skill" / "SKILL.md").write_text("# skill\n", encoding="utf-8")

    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        paa = PackageAutoAssembler(
            module_name=module_name,
            module_filepath=str(module_file),
            add_artifacts=True,
            drawio_class=_DummyDrawioHandler,
            artifacts_class=_DummyArtifactsHandler,
        )

        paa.prepare_artifacts(artifacts_filepaths={})
    finally:
        os.chdir(old_cwd)

    assert ".paa.tracking/skills" in paa.artifacts_h.last_manifest_input
    assert paa.artifacts_h.last_manifest_input[".paa.tracking/skills"] == f"skills/{module_name}"
