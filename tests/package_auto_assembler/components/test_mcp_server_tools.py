import importlib.util
import sys
import types
from pathlib import Path


def _load_mcp_module(monkeypatch):
    fake_mcp_pkg = types.ModuleType("mcp")
    fake_mcp_server_pkg = types.ModuleType("mcp.server")
    fake_fastmcp_module = types.ModuleType("mcp.server.fastmcp")

    class FakeFastMCP:
        def __init__(self, _name):
            self._tool_manager = types.SimpleNamespace(tools={})

        def tool(self):
            def decorator(func):
                self._tool_manager.tools[func.__name__] = func
                return func

            return decorator

    fake_fastmcp_module.FastMCP = FakeFastMCP

    monkeypatch.setitem(sys.modules, "mcp", fake_mcp_pkg)
    monkeypatch.setitem(sys.modules, "mcp.server", fake_mcp_server_pkg)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fake_fastmcp_module)

    fake_paa_module = types.ModuleType("package_auto_assembler")
    fake_paa_module.DependenciesAnalyser = object
    fake_paa_module.ArtifactsHandler = object
    fake_paa_module.CheckpointHandler = object
    fake_paa_module.LocalDependaciesHandler = object
    fake_paa_module.PAA_PATH_DEFAULTS = {}
    monkeypatch.setitem(sys.modules, "package_auto_assembler", fake_paa_module)

    module_path = Path(__file__).resolve().parents[3] / "mcp" / "package_auto_assembler.py"
    spec = importlib.util.spec_from_file_location("paa_mcp_module_for_tests", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_list_package_skills_reads_installed_layout(monkeypatch, tmp_path):
    module = _load_mcp_module(monkeypatch)

    installed_root = tmp_path / "site-packages" / "package_auto_assembler"
    skills_root = installed_root / ".paa.tracking" / "skills" / "package_auto_assembler"
    (skills_root / "z-skill").mkdir(parents=True)
    (skills_root / "z-skill" / "SKILL.md").write_text("# z\n", encoding="utf-8")
    (skills_root / "a-skill").mkdir(parents=True)
    (skills_root / "a-skill" / "SKILL.md").write_text("# a\n", encoding="utf-8")

    monkeypatch.setattr(
        module,
        "_resolve_installed_package_root",
        lambda module_name="package_auto_assembler": installed_root,
    )

    result = module.list_package_skills("package-auto-assembler")

    assert result["ok"] is True
    assert result["module_name"] == "package_auto_assembler"
    assert result["skills"] == ["a-skill", "z-skill"]
    assert result["skills_root"] == str(skills_root)


def test_run_pylint_test_scopes_to_selected_package(monkeypatch, tmp_path):
    module = _load_mcp_module(monkeypatch)
    monkeypatch.chdir(tmp_path)

    module_dir = tmp_path / "python_modules"
    deps_dir = module_dir / "components"
    deps_dir.mkdir(parents=True)
    main_module = module_dir / "package_auto_assembler.py"
    main_module.write_text("x = 1\n", encoding="utf-8")
    dep_module = deps_dir / "dep_a.py"
    dep_module.write_text("y = 1\n", encoding="utf-8")

    installed_root = tmp_path / "site-packages" / "package_auto_assembler"
    script_path = installed_root / "artifacts" / "tools" / "pylint_test.sh"
    script_path.parent.mkdir(parents=True)
    script_path.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")

    monkeypatch.setattr(
        module,
        "_resolve_installed_package_root",
        lambda module_name="package_auto_assembler": installed_root,
    )

    init_args = {}

    class FakeLocalDependaciesHandler:
        def __init__(self, main_module_filepath, dependencies_dir):
            init_args["main_module_filepath"] = main_module_filepath
            init_args["dependencies_dir"] = dependencies_dir

        def get_module_deps_path(self):
            return [str(main_module), str(dep_module)]

    monkeypatch.setattr(module, "LocalDependaciesHandler", FakeLocalDependaciesHandler)

    class FakeCompletedProcess:
        returncode = 0
        stdout = "ok\n"
        stderr = ""

    called = {}

    def fake_run(command, capture_output, text, check):
        called["command"] = command
        called["capture_output"] = capture_output
        called["text"] = text
        called["check"] = check
        return FakeCompletedProcess()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.run_pylint_test(package_name="package-auto-assembler")

    assert result["ok"] is True
    assert result["return_code"] == 0
    assert result["module_dir"] == str(module_dir.resolve())
    assert result["files_to_check"] == [
        str(main_module.resolve()),
        str(dep_module.resolve()),
    ]
    assert called["command"][0] == str(script_path)
    assert called["command"][1:3] == ["--module-directory", str(module_dir.resolve())]
    assert called["command"][3:] == [
        str(main_module.resolve()),
        str(dep_module.resolve()),
    ]
    assert init_args["main_module_filepath"] == str(main_module)
    assert init_args["dependencies_dir"] == str(deps_dir.resolve())
