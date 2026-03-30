from click.testing import CliRunner
from pathlib import Path
import yaml

import cli.package_auto_assembler as paa_cli


class _DummyMetadataHandler:
    def is_metadata_available(self):
        return False


class _DummyLogger:
    def info(self, _msg):
        return None


def _install_dummy_paa(monkeypatch):
    captured = {}

    class _DummyPackageAutoAssembler:
        def __init__(self, **kwargs):
            captured["kwargs"] = kwargs
            self.metadata_h = _DummyMetadataHandler()
            self.logger = _DummyLogger()
            self.default_version = "0.0.0"
            self.setup_directory = kwargs.get("setup_directory", "./tmp")

        def prep_setup_dir(self):
            Path(self.setup_directory).mkdir(parents=True, exist_ok=True)

        def merge_local_dependacies(self):
            return None

        def add_requirements_from_module(self):
            return None

        def add_requirements_from_cli_module(self):
            return None

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPackageAutoAssembler)
    return captured


def test_make_package_defaults_to_dependency_compat_check(monkeypatch):
    captured = _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(paa_cli.cli, ["make-package", "demo_mod"])

    assert result.exit_code == 0, result.output
    assert captured["kwargs"]["check_dependencies_compatibility"] is True
    assert captured["kwargs"]["check_full_dependencies_compatibility"] is True


def test_make_package_skip_flag_disables_dependency_compat_check(monkeypatch):
    captured = _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(
        paa_cli.cli,
        ["make-package", "demo_mod", "--skip-deps-compat-check"],
    )

    assert result.exit_code == 0, result.output
    assert captured["kwargs"]["check_dependencies_compatibility"] is False


def test_make_package_skip_flag_disables_full_dependency_compat_check(monkeypatch):
    captured = _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(
        paa_cli.cli,
        ["make-package", "demo_mod", "--skip-full-deps-compat-check"],
    )

    assert result.exit_code == 0, result.output
    assert captured["kwargs"]["check_full_dependencies_compatibility"] is False


def test_test_install_defaults_to_dependency_compat_check(monkeypatch):
    captured = _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(paa_cli.cli, ["test-install", "demo_mod"])

    assert result.exit_code == 0, result.output
    assert captured["kwargs"]["check_dependencies_compatibility"] is True
    assert captured["kwargs"]["check_full_dependencies_compatibility"] is False


def test_test_install_skip_flag_disables_dependency_compat_check(monkeypatch):
    captured = _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(
        paa_cli.cli,
        ["test-install", "demo_mod", "--skip-deps-compat-check"],
    )

    assert result.exit_code == 0, result.output
    assert captured["kwargs"]["check_dependencies_compatibility"] is False


def test_test_install_flag_enables_full_dependency_compat_check(monkeypatch):
    captured = _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(
        paa_cli.cli,
        ["test-install", "demo_mod", "--check-full-deps-compat"],
    )

    assert result.exit_code == 0, result.output
    assert captured["kwargs"]["check_full_dependencies_compatibility"] is True


def test_check_deps_compat_success_message(monkeypatch):
    _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(paa_cli.cli, ["check-deps-compat", "demo_mod"])

    assert result.exit_code == 0, result.output
    assert "Dependency compatibility checks passed." in result.output


def test_check_deps_compat_full_success_message(monkeypatch):
    _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    result = runner.invoke(paa_cli.cli, ["check-deps-compat", "demo_mod", "--full"])

    assert result.exit_code == 0, result.output
    assert "Dependency compatibility checks passed (static + full resolver)." in result.output


def test_make_package_resolves_license_from_default_licenses_dir(monkeypatch):
    captured = _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        module_name = "demo_mod"
        license_file = Path("licenses") / module_name / "LICENSE"
        license_file.parent.mkdir(parents=True, exist_ok=True)
        license_file.write_text("demo license", encoding="utf-8")

        Path(".paa.config").write_text(
            yaml.safe_dump(
                {
                    "module_dir": "python_modules",
                    "dependencies_dir": "python_modules/components",
                    "licenses_dir": "licenses",
                    "license_path": None,
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        result = runner.invoke(paa_cli.cli, ["make-package", module_name])

    assert result.exit_code == 0, result.output
    assert captured["kwargs"]["license_path"].endswith("licenses/demo_mod/LICENSE")


def test_make_package_resolves_notice_from_default_licenses_dir(monkeypatch):
    captured = _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        module_name = "demo_mod"
        notice_file = Path("licenses") / module_name / "NOTICE"
        notice_file.parent.mkdir(parents=True, exist_ok=True)
        notice_file.write_text("demo notice", encoding="utf-8")

        Path(".paa.config").write_text(
            yaml.safe_dump(
                {
                    "module_dir": "python_modules",
                    "dependencies_dir": "python_modules/components",
                    "licenses_dir": "licenses",
                    "notice_path": None,
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        result = runner.invoke(paa_cli.cli, ["make-package", module_name])

    assert result.exit_code == 0, result.output
    assert captured["kwargs"]["notice_path"].endswith("licenses/demo_mod/NOTICE")


def test_make_package_passes_source_repo_values_from_config(monkeypatch):
    captured = _install_dummy_paa(monkeypatch)
    runner = CliRunner()

    with runner.isolated_filesystem():
        module_name = "demo_mod"
        Path(".paa.config").write_text(
            yaml.safe_dump(
                {
                    "module_dir": "python_modules",
                    "dependencies_dir": "python_modules/components",
                    "source_repo_url": "https://github.com/example/repo",
                    "source_repo_name": "PPR Repo",
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        result = runner.invoke(paa_cli.cli, ["make-package", module_name])

    assert result.exit_code == 0, result.output
    assert captured["kwargs"]["source_repo_url"] == "https://github.com/example/repo"
    assert captured["kwargs"]["source_repo_name"] == "PPR Repo"


def test_extract_module_pyproject_copies_tracked_pep621(monkeypatch):
    runner = CliRunner()

    with runner.isolated_filesystem():
        pkg_root = Path("fake_installed_pkg")
        tracking = pkg_root / ".paa.tracking"
        tracking.mkdir(parents=True, exist_ok=True)
        tracked_pyproject = tracking / "pyproject.toml"
        tracked_pyproject.write_text("[project]\nname = \"demo-mod\"\n", encoding="utf-8")

        monkeypatch.setattr(paa_cli.pkg_resources, "files", lambda _name: pkg_root)

        result = runner.invoke(
            paa_cli.cli,
            [
                "extract-module-pyproject",
                "demo_mod",
                "--format",
                "pep621",
                "--output-path",
                "out.toml",
            ],
        )

        assert result.exit_code == 0, result.output
        assert Path("out.toml").read_text(encoding="utf-8") == "[project]\nname = \"demo-mod\"\n"


def test_extract_module_pyproject_default_filename(monkeypatch):
    runner = CliRunner()

    with runner.isolated_filesystem():
        pkg_root = Path("fake_installed_pkg")
        tracking = pkg_root / ".paa.tracking"
        tracking.mkdir(parents=True, exist_ok=True)
        (tracking / "pyproject.toml").write_text("[project]\nname = \"demo-mod\"\n", encoding="utf-8")

        monkeypatch.setattr(paa_cli.pkg_resources, "files", lambda _name: pkg_root)

        result = runner.invoke(
            paa_cli.cli,
            [
                "extract-module-pyproject",
                "demo_mod",
                "--format",
                "uv",
            ],
        )

        assert result.exit_code == 0, result.output
        assert Path("pyproject.toml").exists()
        assert Path("pyproject.toml").read_text(encoding="utf-8") == "[project]\nname = \"demo-mod\"\n"


def test_extract_module_pyproject_generates_poetry(monkeypatch):
    runner = CliRunner()

    class _DummyDA:
        def get_package_metadata(self, package_name):
            return {
                "version": "1.2.3",
                "author": "Test Author",
                "author_email": "author@example.com",
                "summary": "Demo package",
            }

        def get_package_requirements(self, package_name):
            return ["requests>=2.0", "uvicorn[standard]>=0.30; python_version >= '3.10'"]

    with runner.isolated_filesystem():
        pkg_root = Path("fake_installed_pkg")
        pkg_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(paa_cli.pkg_resources, "files", lambda _name: pkg_root)
        monkeypatch.setattr(paa_cli, "DependenciesAnalyser", _DummyDA)

        result = runner.invoke(
            paa_cli.cli,
            [
                "extract-module-pyproject",
                "demo_mod",
                "--format",
                "poetry",
                "--output-path",
                "poetry.toml",
            ],
        )

        assert result.exit_code == 0, result.output
        content = Path("poetry.toml").read_text(encoding="utf-8")
        assert "[tool.poetry]" in content
        assert 'name = "demo-mod"' in content
        assert '"requests" = ">=2.0"' in content
        assert '"uvicorn" = { version = ">=0.30", extras = ["standard"]' in content
        assert 'markers = "python_version >= \\"3.10\\""' in content
