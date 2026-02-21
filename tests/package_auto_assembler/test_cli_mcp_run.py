from pathlib import Path

import yaml
from click.testing import CliRunner

from cli import package_auto_assembler as cli_module


def test_run_mcp_split_default_no_prefix(monkeypatch):
    captured = {}

    class FakeMcpHandler:
        def __init__(self, loggerLvl=None):
            captured["loggerLvl"] = loggerLvl

        def run_apps(self, **kwargs):
            captured["run_apps"] = kwargs

    monkeypatch.setattr(cli_module, "McpHandler", FakeMcpHandler)

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        [
            "run-mcp",
            "--mcp-config",
            "missing.mcp.config",
            "--package",
            "package-auto-assembler",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["run_apps"]["mode"] == "split"
    assert captured["run_apps"]["server_prefix"] is None
    assert captured["run_apps"]["package_names"] == ["package-auto-assembler"]


def test_run_mcp_split_uses_prefix_when_explicitly_set_in_config(monkeypatch, tmp_path):
    captured = {}

    class FakeMcpHandler:
        def __init__(self, loggerLvl=None):
            captured["loggerLvl"] = loggerLvl

        def run_apps(self, **kwargs):
            captured["run_apps"] = kwargs

    monkeypatch.setattr(cli_module, "McpHandler", FakeMcpHandler)

    mcp_config = tmp_path / ".paa.mcp.config"
    mcp_config.write_text(
        yaml.safe_dump(
            {
                "RUN": {
                    "mode": "split",
                    "server_prefix": "custom-http",
                },
                "SOURCES": {
                    "packages": ["package-auto-assembler"],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        ["run-mcp", "--mcp-config", str(mcp_config)],
    )

    assert result.exit_code == 0, result.output
    assert captured["run_apps"]["mode"] == "split"
    assert captured["run_apps"]["server_prefix"] == "custom-http"
    assert captured["run_apps"]["package_names"] == ["package-auto-assembler"]


def test_run_mcp_combine_default_prefix(monkeypatch):
    captured = {}

    class FakeMcpHandler:
        def __init__(self, loggerLvl=None):
            captured["loggerLvl"] = loggerLvl

        def run_apps(self, **kwargs):
            captured["run_apps"] = kwargs

    monkeypatch.setattr(cli_module, "McpHandler", FakeMcpHandler)

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        [
            "run-mcp",
            "--mcp-config",
            "missing.mcp.config",
            "--package",
            "package-auto-assembler",
            "--mode",
            "combine",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["run_apps"]["mode"] == "combine"
    assert captured["run_apps"]["server_prefix"] == "paa-http"


def test_init_mcp_config_scaffold(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli_module.cli, ["init-mcp-config"])
        assert result.exit_code == 0, result.output
        assert Path(".paa.mcp.config").exists()

        with open(".paa.mcp.config", "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        assert data["RUN"]["mode"] == "split"
        assert data["RUN"]["transport"] == "streamable-http"
        assert data["SOURCES"]["packages"] == []
        assert data["SOURCES"]["paths"] == []

        result_second = runner.invoke(cli_module.cli, ["init-mcp-config"])
        assert result_second.exit_code == 0, result_second.output
        assert "already exists" in result_second.output


def test_init_api_config_scaffold(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli_module.cli, ["init-api-config"])
        assert result.exit_code == 0, result.output
        assert Path(".paa.api.config").exists()

        with open(".paa.api.config", "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        assert data["DESCRIPTION"]["title"] == "PAA API"
        assert data["RUN"]["host"] == "0.0.0.0"
        assert data["RUN"]["port"] == 8000
        assert "allow_origins" in data["MIDDLEWARE"]

        result_second = runner.invoke(cli_module.cli, ["init-api-config"])
        assert result_second.exit_code == 0, result_second.output
        assert "already exists" in result_second.output


def test_init_api_routes_scaffold(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli_module.cli, ["init-api", "your-package-1"])
        assert result.exit_code == 0, result.output
        routes_path = Path("api_routes") / "your_package_1.py"
        assert routes_path.exists()

        initial_content = routes_path.read_text(encoding="utf-8")
        assert "from fastapi import APIRouter" in initial_content
        assert "from your_package_1.your_package_1 import *" in initial_content
        assert 'router = APIRouter(prefix="/your-package-1")' in initial_content

        routes_path.write_text("# custom\n", encoding="utf-8")
        result_no_force = runner.invoke(cli_module.cli, ["init-api", "your-package-1"])
        assert result_no_force.exit_code == 0, result_no_force.output
        assert "already exists" in result_no_force.output
        assert routes_path.read_text(encoding="utf-8") == "# custom\n"

        result_force = runner.invoke(cli_module.cli, ["init-api", "your-package-1", "--force"])
        assert result_force.exit_code == 0, result_force.output
        forced_content = routes_path.read_text(encoding="utf-8")
        assert forced_content != "# custom\n"
        assert "def health()" in forced_content
        assert '@router.get("/version")' in forced_content


def test_init_cli_scaffold(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli_module.cli, ["init-cli", "your-package-1"])
        assert result.exit_code == 0, result.output
        cli_path = Path("cli") / "your_package_1.py"
        assert cli_path.exists()

        initial_content = cli_path.read_text(encoding="utf-8")
        assert "import click" in initial_content
        assert "from your_package_1.your_package_1 import *" in initial_content
        assert '__cli_metadata__ = {' in initial_content
        assert '"name": "your_package_1"' in initial_content
        assert '@click.group()' in initial_content
        assert 'cli.add_command(health, "health")' in initial_content

        cli_path.write_text("# custom\n", encoding="utf-8")
        result_no_force = runner.invoke(cli_module.cli, ["init-cli", "your-package-1"])
        assert result_no_force.exit_code == 0, result_no_force.output
        assert "already exists" in result_no_force.output
        assert cli_path.read_text(encoding="utf-8") == "# custom\n"

        result_force = runner.invoke(cli_module.cli, ["init-cli", "your-package-1", "--force"])
        assert result_force.exit_code == 0, result_force.output
        forced_content = cli_path.read_text(encoding="utf-8")
        assert forced_content != "# custom\n"
        assert "def health():" in forced_content


def test_init_streamlit_config_scaffold(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli_module.cli, ["init-streamlit-config"])
        assert result.exit_code == 0, result.output
        assert Path(".paa.streamlit.config").exists()

        with open(".paa.streamlit.config", "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        assert data["server"]["headless"] is True
        assert data["server"]["port"] == 8501
        assert "theme" in data

        result_second = runner.invoke(cli_module.cli, ["init-streamlit-config"])
        assert result_second.exit_code == 0, result_second.output
        assert "already exists" in result_second.output


def test_init_streamlit_scaffold(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli_module.cli, ["init-streamlit", "your-package-1"])
        assert result.exit_code == 0, result.output
        streamlit_path = Path("streamlit") / "your_package_1.py"
        assert streamlit_path.exists()

        initial_content = streamlit_path.read_text(encoding="utf-8")
        assert "import streamlit as st" in initial_content
        assert "from your_package_1 import *" in initial_content
        assert "st.set_page_config(" in initial_content
        assert 'st.title("your-package-1 app")' in initial_content

        streamlit_path.write_text("# custom\n", encoding="utf-8")
        result_no_force = runner.invoke(cli_module.cli, ["init-streamlit", "your-package-1"])
        assert result_no_force.exit_code == 0, result_no_force.output
        assert "already exists" in result_no_force.output
        assert streamlit_path.read_text(encoding="utf-8") == "# custom\n"

        result_force = runner.invoke(cli_module.cli, ["init-streamlit", "your-package-1", "--force"])
        assert result_force.exit_code == 0, result_force.output
        forced_content = streamlit_path.read_text(encoding="utf-8")
        assert forced_content != "# custom\n"
        assert 'st.caption("Generated by `paa init-streamlit`.")' in forced_content
