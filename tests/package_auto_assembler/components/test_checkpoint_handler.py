from pathlib import Path

from python_modules.components.paa_deps.checkpoint_handler import CheckpointHandler


def _prepare_minimal_module_tree(base_dir: Path, module_name: str = "pkg_a"):
    (base_dir / "python_modules").mkdir(parents=True, exist_ok=True)
    (base_dir / "python_modules" / f"{module_name}.py").write_text(
        '"""module"""\n\ndef f():\n    return 1\n',
        encoding="utf-8",
    )


def test_checkpoint_handler_init_history_repo_creates_git_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    handler = CheckpointHandler()

    git_dir = handler.init_history_repo("pkg-a")

    assert git_dir.exists()
    assert (git_dir / ".git").exists()


def test_checkpoint_handler_create_and_list_checkpoints(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prepare_minimal_module_tree(tmp_path, "pkg_a")

    handler = CheckpointHandler()
    checkpoint = handler.create_checkpoint(
        module_name="pkg-a",
        version_label="0.1.0",
        source_event="manual",
    )

    assert checkpoint["module_name"] == "pkg_a"
    assert checkpoint["changed"] is True
    assert checkpoint["commit"]
    assert checkpoint["tag"] == "v0.1.0"

    checkpoints = handler.list_checkpoints("pkg-a")
    assert len(checkpoints) == 1
    assert checkpoints[0]["commit"] == checkpoint["commit"]
    assert "v0.1.0" in checkpoints[0]["tags"]


def test_checkpoint_handler_noop_when_no_changes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prepare_minimal_module_tree(tmp_path, "pkg_a")

    handler = CheckpointHandler()
    first = handler.create_checkpoint(module_name="pkg-a", version_label="0.0.0", source_event="manual")
    second = handler.create_checkpoint(module_name="pkg-a", version_label="0.0.0", source_event="manual")

    assert first["changed"] is True
    assert second["changed"] is False
    assert second["commit"] == first["commit"]


def test_checkpoint_handler_show_checkpoint_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prepare_minimal_module_tree(tmp_path, "pkg_a")

    handler = CheckpointHandler()
    handler.create_checkpoint(module_name="pkg-a", version_label="0.1.0", source_event="manual")

    module_file = tmp_path / "python_modules" / "pkg_a.py"
    module_file.write_text('"""module"""\n\ndef f():\n    return 2\n', encoding="utf-8")
    handler.create_checkpoint(module_name="pkg-a", version_label="0.1.1", source_event="manual")

    summary = handler.show_checkpoint(module_name="pkg-a", target="latest")

    assert summary["module_name"] == "pkg_a"
    assert summary["commit"]
    assert summary["changed_files_count"] >= 1
    assert summary["modified_count"] >= 1


def test_checkpoint_handler_checkout_plan_defaults_to_latest_stable_tag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prepare_minimal_module_tree(tmp_path, "pkg_a")

    handler = CheckpointHandler()
    handler.create_checkpoint(module_name="pkg-a", version_label="0.0.0", source_event="manual")

    module_file = tmp_path / "python_modules" / "pkg_a.py"
    module_file.write_text('"""module"""\n\ndef f():\n    return 3\n', encoding="utf-8")
    stable = handler.create_checkpoint(module_name="pkg-a", version_label="0.2.0", source_event="manual")

    plan = handler.show_checkout_plan(module_name="pkg-a")

    assert plan["resolved_target"] == "v0.2.0"
    assert plan["target_commit"] == stable["commit"]
    assert plan["would_install"] is True
    assert plan["would_unfold_sync"] is False


def test_checkpoint_handler_apply_checkpoint_to_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prepare_minimal_module_tree(tmp_path, "pkg_a")

    handler = CheckpointHandler()
    handler.create_checkpoint(module_name="pkg-a", version_label="0.1.0", source_event="manual")

    module_file = tmp_path / "python_modules" / "pkg_a.py"
    module_file.write_text('"""modified locally"""\n', encoding="utf-8")

    applied = handler.apply_checkpoint_to_workspace(
        module_name="pkg-a",
        target="v0.1.0",
        workspace_root=".",
        delete_missing=True,
    )

    assert applied["target_commit"]
    restored = module_file.read_text(encoding="utf-8")
    assert 'def f()' in restored
