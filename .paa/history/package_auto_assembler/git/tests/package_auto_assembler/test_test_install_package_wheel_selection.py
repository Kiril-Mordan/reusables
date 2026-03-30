from pathlib import Path

import pytest

from python_modules.package_auto_assembler import PackageAutoAssembler


def _make_paa(tmp_path: Path, module_name: str = "package_auto_assembler") -> PackageAutoAssembler:
    module_file = tmp_path / f"{module_name}.py"
    module_file.write_text("__package_metadata__ = {'name': 'x'}\n", encoding="utf-8")
    return PackageAutoAssembler(
        module_name=module_name,
        module_filepath=str(module_file),
    )


def test_test_install_package_ignores_non_matching_wheels(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "workflow_auto_assembler-0.0.0-py3-none-any.whl").write_text("", encoding="utf-8")
    (dist_dir / "package_auto_assembler-1.2.3-py3-none-any.whl").write_text("", encoding="utf-8")

    installed_cmds = []

    def _fake_run(cmd, check):
        installed_cmds.append(cmd)
        return None

    monkeypatch.setattr("python_modules.package_auto_assembler.subprocess.run", _fake_run)

    paa = _make_paa(tmp_path)
    paa.test_install_package(remove_temp_files=False, skip_deps_install=True)

    assert len(installed_cmds) == 1
    wheel_arg = installed_cmds[0][-1]
    assert wheel_arg == "dist/package_auto_assembler-1.2.3-py3-none-any.whl"


def test_test_install_package_raises_when_only_foreign_wheels_exist(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "workflow_auto_assembler-0.0.0-py3-none-any.whl").write_text("", encoding="utf-8")

    paa = _make_paa(tmp_path)

    with pytest.raises(FileNotFoundError) as exc_info:
        paa.test_install_package(remove_temp_files=False, skip_deps_install=True)

    assert "No wheel file for module 'package_auto_assembler'" in str(exc_info.value)
    assert "workflow_auto_assembler-0.0.0-py3-none-any.whl" in str(exc_info.value)
