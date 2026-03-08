import os

from click.testing import CliRunner

import cli.package_auto_assembler as paa_cli


def test_checkpoint_create_reports_created(monkeypatch):
    runner = CliRunner()
    captured = {}

    class _DummyCheckpointHandler:
        def create_checkpoint(self, module_name, version_label, source_event):
            captured["create_args"] = (module_name, version_label, source_event)
            return {
                "changed": True,
                "commit": "abc123",
                "tag": "v0.1.0",
            }

    class _DummyPAA:
        def __init__(self, **kwargs):
            captured["paa_init"] = kwargs
            self.checkpoint_h = _DummyCheckpointHandler()

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    with runner.isolated_filesystem():
        os.makedirs("python_modules", exist_ok=True)
        with open("python_modules/pkg_a.py", "w", encoding="utf-8") as file:
            file.write("def f():\n    return 1\n")

        result = runner.invoke(
            paa_cli.cli,
            ["checkpoint-create", "pkg-a", "--version-label", "0.1.0", "--source-event", "manual"],
        )

    assert result.exit_code == 0
    assert "Created checkpoint for 'pkg_a' at abc123 (tag: v0.1.0)" in result.output
    assert captured["create_args"] == ("pkg_a", "0.1.0", "manual")


def test_checkpoint_create_reports_no_changes(monkeypatch):
    runner = CliRunner()

    class _DummyCheckpointHandler:
        def create_checkpoint(self, module_name, version_label, source_event):
            return {
                "changed": False,
                "commit": "abc123",
                "tag": None,
            }

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.checkpoint_h = _DummyCheckpointHandler()

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    with runner.isolated_filesystem():
        os.makedirs("python_modules", exist_ok=True)
        with open("python_modules/pkg_a.py", "w", encoding="utf-8") as file:
            file.write("def f():\n    return 1\n")

        result = runner.invoke(
            paa_cli.cli,
            ["checkpoint-create", "pkg-a"],
        )

    assert result.exit_code == 0
    assert "No changes detected for 'pkg_a'. Current checkpoint: abc123" in result.output


def test_checkpoint_list_outputs_rows(monkeypatch):
    runner = CliRunner()

    class _DummyCheckpointHandler:
        def list_checkpoints(self, module_name, limit):
            assert module_name == "pkg_a"
            assert limit == 5
            return [
                {
                    "commit": "abc123",
                    "committed_at": "2026-02-24T00:00:00+00:00",
                    "tags": ["v0.1.0"],
                    "message": "checkpoint[manual] version=0.1.0",
                }
            ]

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.checkpoint_h = _DummyCheckpointHandler()

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    result = runner.invoke(
        paa_cli.cli,
        ["checkpoint-list", "pkg-a", "--limit", "5"],
    )

    assert result.exit_code == 0
    assert "abc123 | 2026-02-24T00:00:00+00:00 | tags=v0.1.0 | checkpoint[manual] version=0.1.0" in result.output


def test_checkpoint_show_outputs_summary(monkeypatch):
    runner = CliRunner()

    class _DummyCheckpointHandler:
        def show_checkpoint(self, module_name, target):
            assert module_name == "pkg_a"
            assert target == "latest"
            return {
                "module_name": "pkg_a",
                "target": "latest",
                "commit": "abc123",
                "committed_at": "2026-02-24T00:00:00+00:00",
                "message": "checkpoint[manual] version=0.1.0",
                "tags": ["v0.1.0"],
                "changed_files_count": 3,
                "added_count": 1,
                "modified_count": 2,
                "deleted_count": 0,
            }

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.checkpoint_h = _DummyCheckpointHandler()

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    result = runner.invoke(
        paa_cli.cli,
        ["checkpoint-show", "pkg-a", "latest"],
    )

    assert result.exit_code == 0
    assert "module: pkg_a" in result.output
    assert "target: latest" in result.output
    assert "commit: abc123" in result.output
    assert "tags: v0.1.0" in result.output
    assert "changes: total=3 added=1 modified=2 deleted=0" in result.output


def test_checkout_dry_run_outputs_plan(monkeypatch):
    runner = CliRunner()

    class _DummyCheckpointHandler:
        def show_checkout_plan(self, module_name, target, unfold, no_install, keep_temp_files):
            assert module_name == "pkg_a"
            assert target is None
            assert unfold is True
            assert no_install is False
            assert keep_temp_files is False
            return {
                "module_name": "pkg_a",
                "target_input": None,
                "resolved_target": "v0.2.0",
                "target_commit": "abc123",
                "would_create_temp_workspace": True,
                "would_unfold_sync": True,
                "would_install": True,
                "would_cleanup_temp": True,
                "files_to_write": ["a.py"],
                "files_to_update": ["b.py", "c.py"],
                "files_to_delete": [],
            }

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.checkpoint_h = _DummyCheckpointHandler()

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    result = runner.invoke(
        paa_cli.cli,
        ["checkout", "pkg-a", "--dry-run", "--unfold"],
    )

    assert result.exit_code == 0
    assert "Checkout plan (dry-run):" in result.output
    assert "resolved_target: v0.2.0" in result.output
    assert "target_commit: abc123" in result.output
    assert "unfold_sync: yes" in result.output
    assert "install: yes" in result.output
    assert "files_to_write: 1" in result.output
    assert "files_to_update: 2" in result.output


def test_checkout_apply_no_install(monkeypatch):
    runner = CliRunner()

    captured = {}

    class _DummyCheckpointHandler:
        def _load_effective_config(self):
            return {"module_dir": "python_modules"}

        def show_checkout_plan(self, module_name, target, unfold, no_install, keep_temp_files):
            return {
                "module_name": module_name,
                "target_input": target,
                "resolved_target": "v0.2.0",
                "target_commit": "abc123",
                "would_create_temp_workspace": True,
                "would_unfold_sync": unfold,
                "would_install": not no_install,
                "would_cleanup_temp": not keep_temp_files,
                "files_to_write": [],
                "files_to_update": [],
                "files_to_delete": [],
            }

        def apply_checkpoint_to_workspace(self, module_name, target, workspace_root, delete_missing, paa_config):
            captured.setdefault("apply_calls", []).append(
                (module_name, target, workspace_root, delete_missing)
            )
            return {
                "resolved_target": "v0.2.0",
                "target_commit": "abc123",
                "written_count": 1,
                "updated_count": 2,
                "deleted_count": 0,
            }

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.checkpoint_h = _DummyCheckpointHandler()

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    result = runner.invoke(
        paa_cli.cli,
        ["checkout", "pkg-a", "--unfold", "--no-install"],
    )

    assert result.exit_code == 0
    assert "Checkout applied for 'pkg_a'." in result.output
    assert "Install step skipped (--no-install)." in result.output
    assert len(captured["apply_calls"]) == 2
    assert captured["apply_calls"][0][2] != "."
    assert captured["apply_calls"][1][2] == "."


def test_checkout_apply_install_failure_is_reported(monkeypatch):
    runner = CliRunner()

    class _DummyCheckpointHandler:
        def _load_effective_config(self):
            return {"module_dir": "python_modules"}

        def show_checkout_plan(self, module_name, target, unfold, no_install, keep_temp_files):
            return {
                "module_name": module_name,
                "target_input": target,
                "resolved_target": "v0.2.0",
                "target_commit": "abc123",
                "would_create_temp_workspace": True,
                "would_unfold_sync": unfold,
                "would_install": not no_install,
                "would_cleanup_temp": not keep_temp_files,
                "files_to_write": [],
                "files_to_update": [],
                "files_to_delete": [],
            }

        def apply_checkpoint_to_workspace(self, module_name, target, workspace_root, delete_missing, paa_config):
            return {
                "resolved_target": "v0.2.0",
                "target_commit": "abc123",
                "written_count": 0,
                "updated_count": 0,
                "deleted_count": 0,
            }

        def show_checkpoint(self, module_name, target):
            return {
                "message": "checkpoint[manual] version=0.2.0 ts=2026-02-25T00:00:00+00:00",
            }

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.checkpoint_h = _DummyCheckpointHandler()

    class _Result:
        returncode = 1
        stdout = "out"
        stderr = "err"

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)
    monkeypatch.setattr(paa_cli.subprocess, "run", lambda *args, **kwargs: _Result())

    result = runner.invoke(
        paa_cli.cli,
        ["checkout", "pkg-a"],
    )

    assert result.exit_code != 0
    assert "Checkout install step failed." in result.output


def test_checkout_apply_install_passes_checkpoint_version(monkeypatch):
    runner = CliRunner()
    captured = {}

    class _DummyCheckpointHandler:
        def _load_effective_config(self):
            return {"module_dir": "python_modules"}

        def show_checkout_plan(self, module_name, target, unfold, no_install, keep_temp_files):
            return {
                "module_name": module_name,
                "target_input": target,
                "resolved_target": "v1.2.3",
                "target_commit": "abc123",
                "would_create_temp_workspace": True,
                "would_unfold_sync": unfold,
                "would_install": not no_install,
                "would_cleanup_temp": not keep_temp_files,
                "files_to_write": [],
                "files_to_update": [],
                "files_to_delete": [],
            }

        def show_checkpoint(self, module_name, target):
            return {
                "message": "checkpoint[manual] version=1.2.3 ts=2026-02-25T00:00:00+00:00",
            }

        def apply_checkpoint_to_workspace(self, module_name, target, workspace_root, delete_missing, paa_config):
            return {
                "resolved_target": "v1.2.3",
                "target_commit": "abc123",
                "written_count": 0,
                "updated_count": 0,
                "deleted_count": 0,
            }

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.checkpoint_h = _DummyCheckpointHandler()

    class _Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(*args, **kwargs):
        captured["cmd"] = args[0]
        return _Result()

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)
    monkeypatch.setattr(paa_cli.subprocess, "run", _fake_run)

    result = runner.invoke(
        paa_cli.cli,
        ["checkout", "pkg-a"],
    )

    assert result.exit_code == 0, result.output
    assert "--default-version" in captured["cmd"]
    idx = captured["cmd"].index("--default-version")
    assert captured["cmd"][idx + 1] == "1.2.3"


def test_make_package_creates_checkpoint_by_default(monkeypatch):
    runner = CliRunner()
    captured = {}

    class _DummyCheckpointHandler:
        def create_checkpoint(self, module_name, version_label, source_event):
            captured["checkpoint"] = (module_name, version_label, source_event)
            return {"changed": True, "commit": "abc123", "tag": "dev-latest"}

        def export_pruned_history(self, module_name, prune_version):
            captured["export_pruned_history"] = (module_name, prune_version)
            return None

    class _DummyMetadataHandler:
        def is_metadata_available(self):
            return True

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.default_version = kwargs.get("default_version", "0.0.0")
            self.metadata = {}
            self.metadata_h = _DummyMetadataHandler()
            self.checkpoint_h = _DummyCheckpointHandler()
            self.logger = type("L", (), {"info": lambda self, _m: None})()

        def add_metadata_from_module(self):
            return None

        def add_metadata_from_cli_module(self):
            return None

        def add_or_update_version(self):
            self.metadata["version"] = "1.2.3"

        def add_or_update_release_notes(self):
            return None

        def prep_setup_dir(self):
            return None

        def merge_local_dependacies(self):
            return None

        def add_requirements_from_module(self):
            return None

        def add_requirements_from_cli_module(self):
            return None

        def add_requirements_from_api_route(self):
            return None

        def add_requirements_from_streamlit(self):
            return None

        def add_requirements_from_mcp(self):
            return None

        def add_readme(self, execute_notebook=False):
            return None

        def add_extra_docs(self):
            return None

        def make_mkdocs_site(self):
            return None

        def prepare_artifacts(self):
            return None

        def prep_setup_file(self):
            return None

        def make_package(self):
            return None

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    result = runner.invoke(paa_cli.cli, ["make-package", "pkg-a"])

    assert result.exit_code == 0, result.output
    assert captured["checkpoint"] == ("pkg_a", "1.2.3", "make-package")
    assert captured["export_pruned_history"] == ("pkg_a", "0.0.0")


def test_make_package_skips_checkpoint_with_no_checkpoint_flag(monkeypatch):
    runner = CliRunner()
    captured = {"calls": 0}

    class _DummyCheckpointHandler:
        def create_checkpoint(self, module_name, version_label, source_event):
            captured["calls"] += 1
            return {"changed": True, "commit": "abc123", "tag": "dev-latest"}

        def export_pruned_history(self, module_name, prune_version):
            captured["export_pruned_history"] = (module_name, prune_version)
            return None

    class _DummyMetadataHandler:
        def is_metadata_available(self):
            return True

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.default_version = kwargs.get("default_version", "0.0.0")
            self.metadata = {}
            self.metadata_h = _DummyMetadataHandler()
            self.checkpoint_h = _DummyCheckpointHandler()
            self.logger = type("L", (), {"info": lambda self, _m: None})()

        def add_metadata_from_module(self):
            return None

        def add_metadata_from_cli_module(self):
            return None

        def add_or_update_version(self):
            self.metadata["version"] = "1.2.3"

        def add_or_update_release_notes(self):
            return None

        def prep_setup_dir(self):
            return None

        def merge_local_dependacies(self):
            return None

        def add_requirements_from_module(self):
            return None

        def add_requirements_from_cli_module(self):
            return None

        def add_requirements_from_api_route(self):
            return None

        def add_requirements_from_streamlit(self):
            return None

        def add_requirements_from_mcp(self):
            return None

        def add_readme(self, execute_notebook=False):
            return None

        def add_extra_docs(self):
            return None

        def make_mkdocs_site(self):
            return None

        def prepare_artifacts(self):
            return None

        def prep_setup_file(self):
            return None

        def make_package(self):
            return None

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    result = runner.invoke(paa_cli.cli, ["make-package", "pkg-a", "--no-checkpoint"])

    assert result.exit_code == 0, result.output
    assert captured["calls"] == 0
    assert captured["export_pruned_history"] == ("pkg_a", "0.0.0")


def test_test_install_creates_checkpoint_only_when_flag_is_set(monkeypatch):
    runner = CliRunner()
    captured = {"calls": []}

    class _DummyCheckpointHandler:
        def create_checkpoint(self, module_name, version_label, source_event):
            captured["calls"].append((module_name, version_label, source_event))
            return {"changed": True, "commit": "abc123", "tag": "dev-latest"}

    class _DummyMetadataHandler:
        def is_metadata_available(self):
            return True

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.default_version = kwargs.get("default_version", "0.0.0")
            self.metadata = {}
            self.metadata_h = _DummyMetadataHandler()
            self.checkpoint_h = _DummyCheckpointHandler()
            self.logger = type("L", (), {"info": lambda self, _m: None})()

        def add_metadata_from_module(self):
            return None

        def add_metadata_from_cli_module(self):
            return None

        def prep_setup_dir(self):
            return None

        def merge_local_dependacies(self):
            return None

        def add_requirements_from_module(self):
            return None

        def add_requirements_from_cli_module(self):
            return None

        def add_requirements_from_api_route(self):
            return None

        def add_requirements_from_streamlit(self):
            return None

        def add_requirements_from_mcp(self):
            return None

        def add_readme(self, execute_notebook=False):
            return None

        def add_extra_docs(self):
            return None

        def make_mkdocs_site(self):
            return None

        def prepare_artifacts(self):
            return None

        def prep_setup_file(self):
            return None

        def make_package(self):
            return None

        def test_install_package(self, remove_temp_files=True):
            return None

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    no_flag_result = runner.invoke(
        paa_cli.cli,
        ["test-install", "pkg-a", "--skip-deps-install"],
    )
    with_flag_result = runner.invoke(
        paa_cli.cli,
        ["test-install", "pkg-a", "--skip-deps-install", "--checkpoint"],
    )

    assert no_flag_result.exit_code == 0, no_flag_result.output
    assert with_flag_result.exit_code == 0, with_flag_result.output
    assert captured["calls"] == [("pkg_a", "0.0.0", "test-install")]


def test_checkpoint_prune_calls_handler(monkeypatch):
    runner = CliRunner()
    captured = {}

    class _DummyCheckpointHandler:
        def prune_checkpoints(self, module_name, prune_commit, prune_version, dry_run):
            captured["args"] = (module_name, prune_commit, prune_version, dry_run)
            return {
                "removed_count": 2,
                "kept_count": 5,
            }

    class _DummyPAA:
        def __init__(self, **kwargs):
            self.checkpoint_h = _DummyCheckpointHandler()

    monkeypatch.setattr(paa_cli, "PackageAutoAssembler", _DummyPAA)

    result = runner.invoke(
        paa_cli.cli,
        ["checkpoint-prune", "pkg-a", "--dry-run"],
    )

    assert result.exit_code == 0
    assert captured["args"] == ("pkg_a", None, None, True)
    assert "removed=2 kept=5" in result.output
