import logging
import shutil
import os
import sys
import copy
import subprocess
import tempfile
import re
from pathlib import Path
import click #==8.1.7
import yaml
import importlib
import importlib.resources as pkg_resources
import ast
from packaging.requirements import Requirement

from package_auto_assembler.package_auto_assembler import (
    PackageAutoAssembler, 
    ReleaseNotesHandler, 
    VersionHandler,
    RequirementsHandler,
    DependenciesAnalyser,
    FastApiHandler,
    ArtifactsHandler,
    PprHandler,
    LocalDependaciesHandler,
    SkillsHandler,
    StreamlitHandler,
    McpHandler,
    PAA_PATH_DEFAULTS)


__cli_metadata__ = {
    "name" : "paa"
}

# Reading paa version
with pkg_resources.path('package_auto_assembler', '__init__.py') as path:
    paa_path = path
with open(paa_path, 'r', encoding = "utf-8") as f:
    paa_init = f.readlines()

paa_version_lines = [line\
    .replace('__version__=', '')\
    .replace("'","")\
    .strip() \
    for line in paa_init if '__version__' in line]
if paa_version_lines:
    paa_version = paa_version_lines[0]


@click.group()
@click.version_option(version=paa_version, prog_name="package-auto-assembler")
@click.pass_context
def cli(ctx):
    """Package Auto Assembler CLI tool."""
    ctx.ensure_object(dict)


def _resolve_package_license_path(config_data: dict, module_name: str):
    explicit_license_path = config_data.get("license_path")
    if explicit_license_path and os.path.exists(explicit_license_path):
        return explicit_license_path

    licenses_dir = config_data.get("licenses_dir")
    if licenses_dir:
        candidate = os.path.join(licenses_dir, module_name, "LICENSE")
        if os.path.exists(candidate):
            return candidate

    return None


def _resolve_package_notice_path(config_data: dict, module_name: str):
    explicit_notice_path = config_data.get("notice_path")
    if explicit_notice_path and os.path.exists(explicit_notice_path):
        return explicit_notice_path

    licenses_dir = config_data.get("licenses_dir")
    if licenses_dir:
        candidate = os.path.join(licenses_dir, module_name, "NOTICE")
        if os.path.exists(candidate):
            return candidate

    return None


def _load_effective_paa_paths(config_path: str = ".paa.config") -> dict:
    config_data = copy.deepcopy(PAA_PATH_DEFAULTS)
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}
        for key, value in loaded.items():
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            config_data[key] = value
    return config_data


def _create_checkpoint_for_run(paa, module_name: str, source_event: str) -> dict:
    version_label = str((paa.metadata or {}).get("version") or paa.default_version or "0.0.0")
    return paa.checkpoint_h.create_checkpoint(
        module_name=module_name,
        version_label=version_label,
        source_event=source_event,
    )


def _extract_checkpoint_version_from_message(message: str):
    if not message:
        return None
    match = re.search(r"\bversion=(\d+\.\d+\.\d+)\b", str(message))
    if not match:
        return None
    return match.group(1)


def _render_mcp_template(module_name: str) -> str:
    return f'''"""
MCP server for {module_name.replace("_", "-")} package.

Run:
    python mcp/{module_name}.py
"""

from mcp.server.fastmcp import FastMCP
from {module_name} import *

mcp = FastMCP("{module_name.replace("_", "-")}-mcp")


@mcp.tool()
def ping(name: str = "world") -> str:
    """Return a basic greeting."""
    return f"pong: hello {{name}}"


@mcp.tool()
def package_name() -> str:
    """Return package name this MCP module belongs to."""
    return "{module_name}"


if __name__ == "__main__":
    mcp.run()
'''


def _render_api_routes_template(module_name: str) -> str:
    package_label = module_name.replace("_", "-")
    return f'''"""
FastAPI routes scaffold for {package_label}.

This file is loaded by:
    paa run-api-routes --route <path_to_this_file>
or from packaged routes via:
    paa run-api-routes --package {package_label}
"""

from fastapi import APIRouter
from {module_name}.{module_name} import *


router = APIRouter(prefix="/{package_label}")


@router.get("/health")
def health() -> dict:
    return {{"status": "ok", "package": "{package_label}"}}


@router.get("/version")
def package_version() -> dict:
    return {{"version": "0.0.0"}}
'''


def _render_cli_template(module_name: str) -> str:
    package_label = module_name.replace("_", "-")
    return f'''"""
CLI scaffold for {package_label}.
"""

import click
from {module_name}.{module_name} import *

__cli_metadata__ = {{
    "name": "{module_name}"
}}


@click.group()
def cli():
    """CLI for {package_label}."""


@click.command()
def health():
    """Basic health command."""
    click.echo("ok")


cli.add_command(health, "health")


if __name__ == "__main__":
    cli()
'''


def _render_streamlit_template(module_name: str) -> str:
    package_label = module_name.replace("_", "-")
    return f'''"""
Streamlit scaffold for {package_label}.
"""

import streamlit as st
from {module_name} import *


st.set_page_config(page_title="{package_label}", layout="wide")
st.title("{package_label} app")
st.caption("Generated by `paa init-streamlit`.")
st.write("Status: ok")
'''


def _detect_agent_target(target: str = None) -> str:
    if target:
        return target.lower()

    current = Path.cwd().resolve()
    codex_detected = False
    claude_detected = False

    for candidate in [current, *current.parents]:
        if (candidate / ".agents").exists() or (candidate / "AGENTS.md").exists():
            codex_detected = True
        if (candidate / ".claude").exists() or (candidate / "CLAUDE.md").exists():
            claude_detected = True

    if codex_detected and claude_detected:
        raise click.ClickException(
            "Both codex and claude targets were detected. Provide --target codex|claude."
        )
    if claude_detected:
        return "claude"
    return "codex"


def _run_registration_command(command: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )


def _register_mcp_server_for_agent(target: str,
                                   server_name: str,
                                   python_path: str,
                                   module_path: str):
    if target == "codex":
        subprocess.run(
            ["codex", "mcp", "remove", server_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        _run_registration_command([
            "codex", "mcp", "add", server_name, "--", python_path, module_path
        ])
        return

    if target == "claude":
        subprocess.run(
            ["claude", "mcp", "remove", server_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        first_err = None
        for cmd in (
            ["claude", "mcp", "add", server_name, "--", python_path, module_path],
            ["claude", "mcp", "add", server_name, python_path, module_path],
        ):
            try:
                _run_registration_command(cmd)
                return
            except Exception as exc:
                if first_err is None:
                    first_err = exc
        raise click.ClickException(
            "Failed to register MCP server with claude CLI. "
            "Ensure Claude Code CLI is installed and supports `claude mcp add`."
        ) from first_err

    raise click.ClickException(f"Unsupported target: {target}")


def _resolve_installed_mcp_module_path(module_name: str) -> str:
    module_name = module_name.replace("-", "_")
    try:
        package = importlib.import_module(module_name)
    except ImportError:
        return None

    package_file = getattr(package, "__file__", None)
    if not package_file:
        return None

    package_dir = os.path.dirname(package_file)
    mcp_path = os.path.join(package_dir, "mcp_server.py")
    if os.path.exists(mcp_path):
        return mcp_path
    return None


@click.command()
@click.argument('package_name')
@click.argument('skill_name')
@click.option('--target',
              'target',
              type=click.Choice(['codex', 'claude'], case_sensitive=False),
              required=False,
              help='Agent target for auto-detected output path.')
@click.option('--output-dir',
              'output_dir',
              type=str,
              required=False,
              help='Destination skills root. If omitted, target path is auto-detected.')
@click.pass_context
def extract_skill(ctx,
        package_name,
        skill_name,
        target,
        output_dir):
    """Extract a single skill from an installed package."""

    sh = SkillsHandler()
    try:
        destination = sh.extract_skill(
            package_name=package_name,
            skill_name=skill_name,
            output_dir=output_dir,
            target=target,
        )
        click.echo(f"Extracted skill '{skill_name}' from '{package_name}' to {destination}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@click.command()
@click.argument('package_name')
@click.option('--target',
              'target',
              type=click.Choice(['codex', 'claude'], case_sensitive=False),
              required=False,
              help='Agent target for auto-detected output path.')
@click.option('--output-dir',
              'output_dir',
              type=str,
              required=False,
              help='Destination skills root. If omitted, target path is auto-detected.')
@click.pass_context
def extract_skills(ctx,
        package_name,
        target,
        output_dir):
    """Extract all skills from an installed package."""

    sh = SkillsHandler()
    try:
        installed, destination = sh.extract_skills(
            package_name=package_name,
            output_dir=output_dir,
            target=target,
        )
        click.echo(f"Extracted {installed} skill(s) from '{package_name}' to {destination}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@click.command()
@click.option('--target',
              'target',
              type=click.Choice(['codex', 'claude'], case_sensitive=False),
              required=False,
              help='Agent target for auto-detected output path.')
@click.option('--output-dir',
              'output_dir',
              type=str,
              required=False,
              help='Skills root to clean. If omitted, target path is auto-detected.')
@click.pass_context
def cleanup_agent_skills(ctx,
        target,
        output_dir):
    """Clean PAA-managed skills from .agents/.claude skills root."""

    sh = SkillsHandler()
    try:
        removed, destination = sh.cleanup_agent_skills(
            output_dir=output_dir,
            target=target,
        )
        click.echo(f"Removed {removed} PAA-managed skill(s) from {destination}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@click.command()
@click.argument('module_name')
@click.option('--version-label',
              'version_label',
              type=str,
              default="0.0.0",
              show_default=True,
              help='Version label to tag checkpoint with.')
@click.option('--source-event',
              'source_event',
              type=str,
              default="manual",
              show_default=True,
              help='Source event label recorded in checkpoint commit message.')
@click.pass_context
def checkpoint_create(ctx,
        module_name,
        version_label,
        source_event):
    """Create a package checkpoint in internal history store."""

    module_name = module_name.replace('-', '_')
    path_config = _load_effective_paa_paths()
    module_filepath = os.path.join(
        path_config.get("module_dir", PAA_PATH_DEFAULTS.get("module_dir", "python_modules")),
        f"{module_name}.py"
    )

    if not os.path.exists(module_filepath):
        click.echo(
            f"Unfolded structure for '{module_name}' was not detected at '{module_filepath}'. "
            "No checkpoint created. Unfold/edit package first, then retry."
        )
        return

    paa = PackageAutoAssembler(
        module_name=module_name,
        module_filepath=module_filepath,
        loggerLvl=logging.INFO
    )

    try:
        result = paa.checkpoint_h.create_checkpoint(
            module_name=module_name,
            version_label=version_label,
            source_event=source_event,
        )
        if result.get("changed"):
            click.echo(
                f"Created checkpoint for '{module_name}' at {result.get('commit')} "
                f"(tag: {result.get('tag')})"
            )
        else:
            click.echo(
                f"No changes detected for '{module_name}'. "
                f"Current checkpoint: {result.get('commit')}"
            )
    except Exception as e:
        raise click.ClickException(str(e)) from e


@click.command()
@click.argument('module_name')
@click.option('--limit',
              'limit',
              type=int,
              default=20,
              show_default=True,
              help='Maximum number of checkpoints to list.')
@click.pass_context
def checkpoint_list(ctx,
        module_name,
        limit):
    """List package checkpoints from internal history store."""

    module_name = module_name.replace('-', '_')
    paa = PackageAutoAssembler(
        module_name=module_name,
        module_filepath=os.path.join(
            PAA_PATH_DEFAULTS.get("module_dir", "python_modules"),
            f"{module_name}.py"
        ),
        loggerLvl=logging.INFO
    )

    try:
        checkpoints = paa.checkpoint_h.list_checkpoints(
            module_name=module_name,
            limit=limit
        )
        if not checkpoints:
            click.echo(f"No checkpoints found for '{module_name}'.")
            return

        for item in checkpoints:
            tags = ",".join(item.get("tags", [])) if item.get("tags") else "-"
            click.echo(
                f"{item.get('commit')} | {item.get('committed_at')} | tags={tags} | {item.get('message')}"
            )
    except Exception as e:
        raise click.ClickException(str(e)) from e


@click.command()
@click.argument('module_name')
@click.argument('target', required=False, default="latest")
@click.pass_context
def checkpoint_show(ctx,
        module_name,
        target):
    """Show details for a specific checkpoint target."""

    module_name = module_name.replace('-', '_')
    paa = PackageAutoAssembler(
        module_name=module_name,
        module_filepath=os.path.join(
            PAA_PATH_DEFAULTS.get("module_dir", "python_modules"),
            f"{module_name}.py"
        ),
        loggerLvl=logging.INFO
    )

    try:
        item = paa.checkpoint_h.show_checkpoint(module_name=module_name, target=target)
        tags = ",".join(item.get("tags", [])) if item.get("tags") else "-"
        click.echo(f"module: {item.get('module_name')}")
        click.echo(f"target: {item.get('target')}")
        click.echo(f"commit: {item.get('commit')}")
        click.echo(f"committed_at: {item.get('committed_at')}")
        click.echo(f"tags: {tags}")
        click.echo(f"message: {item.get('message')}")
        click.echo(
            "changes: "
            f"total={item.get('changed_files_count')} "
            f"added={item.get('added_count')} "
            f"modified={item.get('modified_count')} "
            f"deleted={item.get('deleted_count')}"
        )
    except Exception as e:
        raise click.ClickException(str(e)) from e


@click.command()
@click.argument('module_name')
@click.option('--commit',
              'prune_commit',
              type=str,
              required=False,
              help='Specific checkpoint commit (or prefix) to remove.')
@click.option('--version',
              'prune_version',
              type=str,
              required=False,
              help='Remove checkpoints for a specific version label.')
@click.option('--dry-run',
              'dry_run',
              is_flag=True,
              type=bool,
              required=False,
              help='Show what would be pruned without changing history.')
@click.pass_context
def checkpoint_prune(ctx,
        module_name,
        prune_commit,
        prune_version,
        dry_run):
    """Prune local checkpoint history."""

    if prune_commit and prune_version:
        raise click.ClickException("Use either --commit or --version, not both.")

    module_name = module_name.replace('-', '_')
    paa = PackageAutoAssembler(
        module_name=module_name,
        module_filepath=os.path.join(
            PAA_PATH_DEFAULTS.get("module_dir", "python_modules"),
            f"{module_name}.py"
        ),
        loggerLvl=logging.INFO
    )

    try:
        result = paa.checkpoint_h.prune_checkpoints(
            module_name=module_name,
            prune_commit=prune_commit,
            prune_version=prune_version,
            dry_run=dry_run,
        )
        click.echo(
            f"Checkpoint prune {'plan' if dry_run else 'completed'} for '{module_name}': "
            f"removed={result.get('removed_count')} kept={result.get('kept_count')}"
        )
    except Exception as e:
        raise click.ClickException(str(e)) from e


@click.command()
@click.argument('module_name')
@click.argument('target', required=False, default=None)
@click.option('--unfold', 'unfold', is_flag=True, type=bool, required=False, help='If checked, plan includes syncing checked out files into unfolded structure.')
@click.option('--no-install', 'no_install', is_flag=True, type=bool, required=False, help='If checked, skip install step in the checkout plan.')
@click.option('--dry-run', 'dry_run', is_flag=True, type=bool, required=False, help='If checked, only prints checkout plan without applying changes.')
@click.option('--keep-temp-files', 'keep_temp_files', is_flag=True, type=bool, required=False, help='If checked, temp workspace cleanup is disabled in the plan.')
@click.pass_context
def checkout(ctx,
        module_name,
        target,
        unfold,
        no_install,
        dry_run,
        keep_temp_files):
    """Checkout package checkpoint."""

    module_name = module_name.replace('-', '_')
    paa = PackageAutoAssembler(
        module_name=module_name,
        module_filepath=os.path.join(
            PAA_PATH_DEFAULTS.get("module_dir", "python_modules"),
            f"{module_name}.py"
        ),
        loggerLvl=logging.INFO
    )

    try:
        plan = paa.checkpoint_h.show_checkout_plan(
            module_name=module_name,
            target=target,
            unfold=unfold,
            no_install=no_install,
            keep_temp_files=keep_temp_files,
        )
    except Exception as e:
        raise click.ClickException(str(e)) from e

    if dry_run:
        click.echo("Checkout plan (dry-run):")
        click.echo(f"  module: {plan.get('module_name')}")
        click.echo(f"  target_input: {plan.get('target_input')}")
        click.echo(f"  resolved_target: {plan.get('resolved_target')}")
        click.echo(f"  target_commit: {plan.get('target_commit')}")
        click.echo(f"  temp_workspace: {'yes' if plan.get('would_create_temp_workspace') else 'no'}")
        click.echo(f"  unfold_sync: {'yes' if plan.get('would_unfold_sync') else 'no'}")
        click.echo(f"  install: {'yes' if plan.get('would_install') else 'no'}")
        click.echo(f"  cleanup_temp: {'yes' if plan.get('would_cleanup_temp') else 'no'}")
        click.echo(f"  files_to_write: {len(plan.get('files_to_write', []))}")
        click.echo(f"  files_to_update: {len(plan.get('files_to_update', []))}")
        click.echo(f"  files_to_delete: {len(plan.get('files_to_delete', []))}")
        return

    temp_workspace = tempfile.mkdtemp(prefix=f"paa_checkout_{module_name}_")
    config_data = paa.checkpoint_h._load_effective_config()
    try:
        temp_apply = paa.checkpoint_h.apply_checkpoint_to_workspace(
            module_name=module_name,
            target=target,
            workspace_root=temp_workspace,
            delete_missing=False,
            paa_config=config_data,
        )

        temp_config_path = os.path.join(temp_workspace, ".paa.config")
        with open(temp_config_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(config_data, file, sort_keys=False)

        unfold_apply = None
        if unfold:
            unfold_apply = paa.checkpoint_h.apply_checkpoint_to_workspace(
                module_name=module_name,
                target=target,
                workspace_root=".",
                delete_missing=True,
                paa_config=config_data,
            )

        if not no_install:
            target_details = paa.checkpoint_h.show_checkpoint(
                module_name=module_name,
                target=plan.get("resolved_target") or target or "latest",
            )
            target_version = _extract_checkpoint_version_from_message(target_details.get("message"))
            if not target_version:
                target_version = "0.0.0"
                click.echo(
                    "Warning: could not resolve checkpoint version from history message; "
                    "falling back to 0.0.0 for install step."
                )

            command = [
                "paa",
                "test-install",
                module_name.replace("_", "-"),
                "--skip-deps-install",
                "--config",
                temp_config_path,
                "--default-version",
                target_version,
            ]
            if keep_temp_files:
                command.append("--keep-temp-files")

            result = subprocess.run(
                command,
                cwd=temp_workspace,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise click.ClickException(
                    "Checkout install step failed.\n"
                    f"Command: {' '.join(command)}\n"
                    f"STDOUT:\n{result.stdout}\n"
                    f"STDERR:\n{result.stderr}"
                )

        click.echo(f"Checkout applied for '{module_name}'.")
        click.echo(f"Resolved target: {temp_apply.get('resolved_target')} @ {temp_apply.get('target_commit')}")
        if unfold_apply is not None:
            click.echo(
                "Unfold sync changes: "
                f"written={unfold_apply.get('written_count')} "
                f"updated={unfold_apply.get('updated_count')} "
                f"deleted={unfold_apply.get('deleted_count')}"
            )
        if no_install:
            click.echo("Install step skipped (--no-install).")
        else:
            click.echo("Install step completed from temporary checkout workspace.")
    finally:
        if not keep_temp_files:
            shutil.rmtree(temp_workspace, ignore_errors=True)


def _escape_toml_string(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _render_poetry_pyproject(package_name: str, package_metadata: dict, requirements: list) -> str:
    dist_name = package_name.replace("_", "-")
    version = package_metadata.get("version") or "0.0.0"
    description = _escape_toml_string(package_metadata.get("summary") or "")
    author = package_metadata.get("author")
    author_email = package_metadata.get("author_email")

    lines = []
    lines.append("[tool.poetry]")
    lines.append(f'name = "{_escape_toml_string(dist_name)}"')
    lines.append(f'version = "{_escape_toml_string(version)}"')
    lines.append(f'description = "{description}"')
    if author or author_email:
        if author and author_email:
            lines.append(f'authors = ["{_escape_toml_string(author)} <{_escape_toml_string(author_email)}>"]')
        elif author:
            lines.append(f'authors = ["{_escape_toml_string(author)}"]')
        else:
            lines.append(f'authors = ["<{_escape_toml_string(author_email)}>"]')
    else:
        lines.append('authors = []')

    lines.append("")
    lines.append("[tool.poetry.dependencies]")
    lines.append('python = ">=3.8"')

    parsed_requirements = {}
    for req_line in requirements or []:
        try:
            req = Requirement(req_line)
        except Exception:
            continue

        dep_name = req.name.replace("_", "-")
        spec = str(req.specifier) if str(req.specifier) else "*"
        extras = sorted(req.extras) if req.extras else []
        marker = str(req.marker) if req.marker else None

        if extras or marker:
            fields = [f'version = "{_escape_toml_string(spec)}"']
            if extras:
                extras_str = ", ".join(f'"{_escape_toml_string(x)}"' for x in extras)
                fields.append(f"extras = [{extras_str}]")
            if marker:
                fields.append(f'markers = "{_escape_toml_string(marker)}"')
            parsed_requirements[dep_name] = "{ " + ", ".join(fields) + " }"
        else:
            parsed_requirements[dep_name] = f'"{_escape_toml_string(spec)}"'

    for dep_name in sorted(parsed_requirements.keys(), key=lambda x: x.lower()):
        lines.append(f'"{_escape_toml_string(dep_name)}" = {parsed_requirements[dep_name]}')

    lines.append("")
    lines.append("[build-system]")
    lines.append('requires = ["poetry-core>=1.0.0"]')
    lines.append('build-backend = "poetry.core.masonry.api"')

    return "\n".join(lines) + "\n"


test_install_config_minimal = {
    "module_dir" : PAA_PATH_DEFAULTS.get("module_dir", "python_modules"),
    "example_notebooks_path" : PAA_PATH_DEFAULTS.get("example_notebooks_path", "example_notebooks"),
    "dependencies_dir" : PAA_PATH_DEFAULTS.get("dependencies_dir", "python_modules/components"),
    "licenses_dir": PAA_PATH_DEFAULTS.get("licenses_dir", "licenses"),
    "mcp_dir": PAA_PATH_DEFAULTS.get("mcp_dir", "mcp"),
    "license_path" : None,
    "notice_path" : None,
    "use_commit_messages" : True,
    "check_vulnerabilities" : True,
    "check_dependencies_licenses" : False,
    "make_package_check_dependencies_compatibility": True,
    "test_install_check_dependencies_compatibility": True,
    "make_package_check_full_dependencies_compatibility": True,
    "test_install_check_full_dependencies_compatibility": False,
    "add_artifacts" : True,
    "add_mkdocs_site" : False,
    "classifiers" : None
}

test_install_config = {
    "module_dir" : PAA_PATH_DEFAULTS.get("module_dir", "python_modules"),
    "example_notebooks_path" : PAA_PATH_DEFAULTS.get("example_notebooks_path", "example_notebooks"),
    "dependencies_dir" : PAA_PATH_DEFAULTS.get("dependencies_dir", "python_modules/components"),
    "licenses_dir": PAA_PATH_DEFAULTS.get("licenses_dir", "licenses"),
    "cli_dir" : PAA_PATH_DEFAULTS.get("cli_dir", "cli"),
    "mcp_dir" : PAA_PATH_DEFAULTS.get("mcp_dir", "mcp"),
    "api_routes_dir" : PAA_PATH_DEFAULTS.get("api_routes_dir", "api_routes"),
    "streamlit_dir" : PAA_PATH_DEFAULTS.get("streamlit_dir", "streamlit"),
    "artifacts_dir" : PAA_PATH_DEFAULTS.get("artifacts_dir", "artifacts"),
    "drawio_dir" : PAA_PATH_DEFAULTS.get("drawio_dir", "drawio"),
    "extra_docs_dir" : PAA_PATH_DEFAULTS.get("extra_docs_dir", "extra_docs"),
    "tests_dir" : PAA_PATH_DEFAULTS.get("tests_dir", "tests"),
    "use_commit_messages" : True,
    "check_vulnerabilities" : True,
    "check_dependencies_licenses" : False,
    "make_package_check_dependencies_compatibility": True,
    "test_install_check_dependencies_compatibility": True,
    "make_package_check_full_dependencies_compatibility": True,
    "test_install_check_full_dependencies_compatibility": False,
    "add_artifacts" : True,
    "add_mkdocs_site" : False,
    "license_path" : None,
    "notice_path" : None,
    "license_label" : None,
    "license_badge" : None,
    "allowed_licenses" : None,
    "docs_url" : None,
    "source_repo_url" : None,
    "source_repo_name" : None,
    "classifiers" : None
}

# Config templates used only when generating fresh .paa.config files.
init_config_minimal = {
    "use_commit_messages": True,
    "check_vulnerabilities": True,
    "check_dependencies_licenses": False,
    "add_artifacts": True,
    "add_mkdocs_site": False,
    "pylint_threshold": 8.0,
}

init_config_full = {
    # Paths
    "module_dir": PAA_PATH_DEFAULTS.get("module_dir", "python_modules"),
    "dependencies_dir": PAA_PATH_DEFAULTS.get("dependencies_dir", "python_modules/components"),
    "example_notebooks_path": PAA_PATH_DEFAULTS.get("example_notebooks_path", "example_notebooks"),
    "licenses_dir": PAA_PATH_DEFAULTS.get("licenses_dir", "licenses"),
    "cli_dir": PAA_PATH_DEFAULTS.get("cli_dir", "cli"),
    "mcp_dir": PAA_PATH_DEFAULTS.get("mcp_dir", "mcp"),
    "api_routes_dir": PAA_PATH_DEFAULTS.get("api_routes_dir", "api_routes"),
    "streamlit_dir": PAA_PATH_DEFAULTS.get("streamlit_dir", "streamlit"),
    "artifacts_dir": PAA_PATH_DEFAULTS.get("artifacts_dir", "artifacts"),
    "drawio_dir": PAA_PATH_DEFAULTS.get("drawio_dir", "drawio"),
    "extra_docs_dir": PAA_PATH_DEFAULTS.get("extra_docs_dir", "extra_docs"),
    "tests_dir": PAA_PATH_DEFAULTS.get("tests_dir", "tests"),
    # Core behavior
    "use_commit_messages": True,
    "check_vulnerabilities": True,
    "check_dependencies_licenses": False,
    "add_artifacts": True,
    "add_mkdocs_site": False,
    "pylint_threshold": 8.0,
    # Optional compatibility settings (explicitly shown in full)
    "make_package_check_dependencies_compatibility": None,
    "test_install_check_dependencies_compatibility": None,
    "make_package_check_full_dependencies_compatibility": None,
    "test_install_check_full_dependencies_compatibility": None,
    # Optional metadata/repo settings (explicitly shown in full)
    "license_path": None,
    "notice_path": None,
    "license_label": None,
    "license_badge": None,
    "allowed_licenses": None,
    "docs_url": None,
    "source_repo_url": None,
    "source_repo_name": None,
    "classifiers": None,
}

init_mcp_config_default = {
    "RUN": {
        "host": "127.0.0.1",
        "port": 8000,
        "transport": "streamable-http",
        "mount_path": None,
        "mode": "split",
        "server_prefix": None,
    },
    "SOURCES": {
        "packages": [],
        "paths": [],
    },
}

init_api_config_default = {
    "DESCRIPTION": {
        "title": "PAA API",
        "description": "API routes served by package-auto-assembler.",
        "version": "0.0.0",
    },
    "MIDDLEWARE": {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    },
    "RUN": {
        "host": "0.0.0.0",
        "port": 8000,
    },
}

init_streamlit_config_default = {
    "server": {
        "headless": True,
        "port": 8501,
        "address": "0.0.0.0",
    },
    "theme": {
        "base": "light",
    },
}


def _render_full_init_config_with_comments(config_data: dict) -> str:
    lines = [
        "# Paths",
        f"module_dir: {config_data.get('module_dir')}",
        f"dependencies_dir: {config_data.get('dependencies_dir')}",
        f"example_notebooks_path: {config_data.get('example_notebooks_path')}",
        f"licenses_dir: {config_data.get('licenses_dir')}",
        f"cli_dir: {config_data.get('cli_dir')}",
        f"mcp_dir: {config_data.get('mcp_dir')}",
        f"api_routes_dir: {config_data.get('api_routes_dir')}",
        f"streamlit_dir: {config_data.get('streamlit_dir')}",
        f"artifacts_dir: {config_data.get('artifacts_dir')}",
        f"drawio_dir: {config_data.get('drawio_dir')}",
        f"extra_docs_dir: {config_data.get('extra_docs_dir')}",
        f"tests_dir: {config_data.get('tests_dir')}",
        "",
        "# Core behavior",
        f"use_commit_messages: {str(config_data.get('use_commit_messages')).lower()}",
        f"check_vulnerabilities: {str(config_data.get('check_vulnerabilities')).lower()}",
        f"check_dependencies_licenses: {str(config_data.get('check_dependencies_licenses')).lower()}",
        f"add_artifacts: {str(config_data.get('add_artifacts')).lower()}",
        f"add_mkdocs_site: {str(config_data.get('add_mkdocs_site')).lower()}",
        f"pylint_threshold: {config_data.get('pylint_threshold')}",
        "",
        "# Optional compatibility settings",
        "make_package_check_dependencies_compatibility: null",
        "test_install_check_dependencies_compatibility: null",
        "make_package_check_full_dependencies_compatibility: null",
        "test_install_check_full_dependencies_compatibility: null",
        "",
        "# Optional license related settings",
        "license_path: null",
        "notice_path: null",
        "license_label: null",
        "license_badge: null",
        "allowed_licenses: null",
        "",
        "# Optional docs/repository metadata",
        "docs_url: null",
        "source_repo_url: null",
        "source_repo_name: null",
        "classifiers: null",
        "",
    ]
    return "\n".join(lines)


def _write_init_config(config_path: str, full: bool) -> None:
    if full:
        config_body = _render_full_init_config_with_comments(copy.deepcopy(init_config_full))
        with open(config_path, "w", encoding="utf-8") as file:
            file.write(config_body)
        return

    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(copy.deepcopy(init_config_minimal), file, sort_keys=False)


def _write_mcp_config(config_path: str) -> None:
    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(copy.deepcopy(init_mcp_config_default), file, sort_keys=False)


def _write_api_config(config_path: str) -> None:
    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(copy.deepcopy(init_api_config_default), file, sort_keys=False)


def _write_streamlit_config(config_path: str) -> None:
    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(copy.deepcopy(init_streamlit_config_default), file, sort_keys=False)

@click.command()
@click.option('--full', 'full', is_flag=True, type=bool, 
required=False, help='If checked, dirs beyond essential would be mapped.')
@click.pass_context
def init_config(ctx, full):
    """Initialize config file"""

    config = ".paa.config"

    if not os.path.exists(".paa.config"):
        _write_init_config(config_path=config, full=full)

        click.echo(f"Config file {config} initialized!")
        click.echo(f"Edit it to your preferance.")
    else:
        click.echo(f"Config file already exists in {config}!")


@click.command()
@click.option('--config', 'config_path', type=str, required=False, default=".paa.mcp.config",
              show_default=True, help='Path to mcp config scaffold file.')
@click.option('--force', 'force', is_flag=True, type=bool, required=False,
              help='If checked, existing mcp config will be overwritten.')
@click.pass_context
def init_mcp_config(ctx, config_path, force):
    """Initialize MCP run config file."""

    if os.path.exists(config_path) and not force:
        click.echo(f"MCP config already exists in {config_path}! Use --force to overwrite.")
        return

    _write_mcp_config(config_path=config_path)
    click.echo(f"MCP config file {config_path} initialized!")
    click.echo("Edit SOURCES.packages / SOURCES.paths and optional RUN settings.")


@click.command()
@click.option('--config', 'config_path', type=str, required=False, default=".paa.api.config",
              show_default=True, help='Path to api config scaffold file.')
@click.option('--force', 'force', is_flag=True, type=bool, required=False,
              help='If checked, existing api config will be overwritten.')
@click.pass_context
def init_api_config(ctx, config_path, force):
    """Initialize API run config file."""

    if os.path.exists(config_path) and not force:
        click.echo(f"API config already exists in {config_path}! Use --force to overwrite.")
        return

    _write_api_config(config_path=config_path)
    click.echo(f"API config file {config_path} initialized!")
    click.echo("Edit DESCRIPTION, MIDDLEWARE and RUN settings.")


@click.command()
@click.option('--config', 'config_path', type=str, required=False, default=".paa.streamlit.config",
              show_default=True, help='Path to streamlit config scaffold file.')
@click.option('--force', 'force', is_flag=True, type=bool, required=False,
              help='If checked, existing streamlit config will be overwritten.')
@click.pass_context
def init_streamlit_config(ctx, config_path, force):
    """Initialize Streamlit run config file."""

    if os.path.exists(config_path) and not force:
        click.echo(f"Streamlit config already exists in {config_path}! Use --force to overwrite.")
        return

    _write_streamlit_config(config_path=config_path)
    click.echo(f"Streamlit config file {config_path} initialized!")
    click.echo("Edit server and theme settings.")


@click.command()
@click.option('--full', 'full', is_flag=True, type=bool, 
required=False, help='If checked, dirs beyond essential would be mapped.')
@click.pass_context
def init_paa(ctx, full):
    """Initialize paa tracking files and directores from .paa.config"""

    if not os.path.exists(".paa.config"):
        _write_init_config(config_path=".paa.config", full=full)
        click.echo(".paa.config initialized. Run `paa init-paa` again to create default directories.")
        return

    st = PprHandler().init_paa_dir()

    PprHandler().init_from_paa_config(default_config = copy.deepcopy(test_install_config))

    if st:
        click.echo(f"PAA tracking files initialized!")


@click.command()
@click.option('--github', 'github', is_flag=True, type=bool, required=False, help='If checked, git actions template would be set up.')
@click.option('--azure', 'azure', is_flag=True, type=bool, required=False, help='If checked, azure devops pipelines template would be set up.')
@click.option('--full', 'full', is_flag=True, type=bool, 
required=False, help='If checked, dirs beyond essential would be mapped.')
@click.pass_context
def init_ppr(ctx,
    github,
    azure,
    full):
    """Initialize ppr for a given workflows platform."""

    workflows_platform = None
    if github:
        workflows_platform = 'github'
    if azure:
        workflows_platform = 'azure'

    config_created = False

    if workflows_platform:

        default_config = copy.deepcopy(test_install_config if full else test_install_config_minimal)

        if workflows_platform == 'github':
            default_config.update({'gh_pages_base_url' : None,
                                   'docker_username' : None})

        if not os.path.exists('.paa.config'):
            _write_init_config(config_path=".paa.config", full=full)
            config_created = True
        else:
            PprHandler().init_from_paa_config(default_config = default_config)


    st = PprHandler().init_ppr_repo(workflows_platform = workflows_platform)

    if st:
        click.echo(f"PPR for {workflows_platform} initialized!")
        if config_created:
            click.echo(
                f".paa.config initialized. Next you can run either "
                f"`paa init-ppr --{workflows_platform}` or `paa init-paa` "
                f"to initialize directories from config."
            )
    else:
        click.echo(f"Select workflow type for ppr!")


@click.command()
@click.argument('module_name')
@click.option('--debug', is_flag=True, type=bool, required=False, help='If checked, debug messages will be shown.')
@click.pass_context
def unfold_package(ctx,
        module_name,
        debug):

    """Unfold paa package inside ppr"""

    if debug:
        loggerLvl = logging.DEBUG
    else:
        loggerLvl = logging.INFO

    status = PprHandler(
        loggerLvl = loggerLvl
    ).unfold_package(module_name = module_name)

    if status == 2:
        click.echo(f"Package does not have .paa.tracking !")
    
    if status == 1:
        click.echo(f"Package was not found!")

@click.command()
@click.argument('module_name')
@click.option('--debug', is_flag=True, type=bool, required=False, help='If checked, debug messages will be shown.')
@click.pass_context
def remove_package(ctx,
        module_name,
        debug):

    """Remove paa package from ppr"""

    if debug:
        loggerLvl = logging.DEBUG
    else:
        loggerLvl = logging.INFO

    status = PprHandler(
        paa_config = test_install_config,
        loggerLvl = loggerLvl
    ).remove_package(module_name = module_name)

    
    if status == 1:
        click.echo(f".paa.config was not found!")

@click.command()
@click.argument('module_name')
@click.argument('new_module_name')
@click.option('--debug', is_flag=True, type=bool, required=False, help='If checked, debug messages will be shown.')
@click.pass_context
def rename_package(ctx,
        module_name,
        new_module_name,
        debug):

    """Rename paa package in ppr"""

    if debug:
        loggerLvl = logging.DEBUG
    else:
        loggerLvl = logging.INFO

    status = PprHandler(
        paa_config = test_install_config,
        loggerLvl = loggerLvl
    ).rename_package(
        module_name = module_name,
        new_module_name = new_module_name)

    
    if status == 1:
        click.echo(f".paa.config was not found!")


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--fastapi-routes-filepath', 'fastapi_routes_filepath',  type=str, required=False, help='Path to .py file that routes for fastapi.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--default-version', 'default_version', type=str, required=False, help='Default version.')
@click.option('--check-vulnerabilities', 'check_vulnerabilities', is_flag=True, type=bool, required=False, help='If checked, checks module dependencies with pip-audit for vulnerabilities.')
@click.option('--skip-deps-compat-check', 'skip_deps_compat_check', is_flag=True, type=bool, required=False, help='If checked, skips dependency compatibility check.')
@click.option('--check-full-deps-compat', 'check_full_deps_compat', is_flag=True, type=bool, required=False, help='If checked, runs full dependency resolver compatibility check.')
@click.option('--build-mkdocs', 'build_mkdocs', is_flag=True, type=bool, required=False, help='If checked, builds mkdocs documentation.')
@click.option('--check-licenses', 'check_licenses', is_flag=True, type=bool, required=False, help='If checked, checks module dependencies licenses.')
@click.option('--keep-temp-files', 'keep_temp_files', is_flag=True, type=bool, required=False, help='If checked, setup directory won\'t be removed after setup is done.')
@click.option('--skip-deps-install', 'skip_deps_install', is_flag=True, type=bool, required=False, help='If checked, existing dependencies from env will be reused.')
@click.option('--checkpoint', 'checkpoint', is_flag=True, type=bool, required=False, help='If checked, creates checkpoint before package build/install.')
@click.pass_context
def test_install(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        fastapi_routes_filepath,
        dependencies_dir,
        default_version,
        check_vulnerabilities,
        skip_deps_compat_check,
        check_full_deps_compat,
        build_mkdocs,
        check_licenses,
        skip_deps_install,
        checkpoint,
        keep_temp_files):
    """Test install module into local environment."""

    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    resolved_module_dir = test_install_config.get(
        "module_dir", PAA_PATH_DEFAULTS.get("module_dir", "python_modules")
    )

    test_install_config["loggerLvl"] = logging.INFO

    paa_params = {
        "config_filepath" : config,
        "module_name" : f"{module_name}",
        "module_filepath" : os.path.join(resolved_module_dir, f"{module_name}.py"),
        #"mapping_filepath" : test_install_config.get("mapping_filepath"),
        #"licenses_filepath" : test_install_config.get("licenses_filepath"),
        "dependencies_dir" : test_install_config.get("dependencies_dir"),
        "setup_directory" : f"./{module_name}",
        "add_artifacts" : test_install_config.get("add_artifacts"),
        "artifacts_filepaths" : test_install_config.get("artifacts_filepaths"),
        #"docs_path" : test_install_config.get("docs_dir"),
        "license_badge" : test_install_config.get("license_badge"),
        "license_label" : test_install_config.get("license_label", None),
        "source_repo_url" : test_install_config.get("source_repo_url", None),
        "source_repo_name" : test_install_config.get("source_repo_name", None),
        "release_notes_filepath" : os.path.join('.paa/release_notes',
                                                            f"{module_name}.md"),
    "add_mkdocs_site" : False,
    "license_path": _resolve_package_license_path(test_install_config, module_name),
    "notice_path": _resolve_package_notice_path(test_install_config, module_name),
    "check_dependencies_licenses" : False,
        "check_vulnerabilities" : False,
        "check_dependencies_compatibility": test_install_config.get("test_install_check_dependencies_compatibility", True),
        "check_full_dependencies_compatibility": test_install_config.get("test_install_check_full_dependencies_compatibility", False)

    }


    if test_install_config.get("extra_docs_dir"):
        paa_params["extra_docs_dir"] = os.path.join(
            test_install_config['extra_docs_dir'], f"{module_name}")
        
    if test_install_config.get("tests_dir"):
        paa_params["tests_dir"] = os.path.join(
            test_install_config['tests_dir'], f"{module_name}")

    if test_install_config.get("drawio_dir"):
        paa_params["drawio_filepath"] = os.path.join(
            test_install_config['drawio_dir'], f"{module_name}.drawio")

        paa_params["drawio_dir"] = test_install_config["drawio_dir"]

    if test_install_config.get("example_notebooks_path"):
        paa_params["example_notebook_path"] = os.path.join(test_install_config["example_notebooks_path"],
                                                           f"{module_name}.ipynb")

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("allowed_licenses"):
        paa_params["allowed_licenses"] = test_install_config["allowed_licenses"]

    if test_install_config.get("cli_dir"):
        paa_params["cli_module_filepath"] = os.path.join(
            test_install_config['cli_dir'], f"{module_name}.py")

    if test_install_config.get("api_routes_dir"):
        paa_params["fastapi_routes_filepath"] = os.path.join(
            test_install_config['api_routes_dir'], f"{module_name}.py")

    if test_install_config.get("streamlit_dir"):
        paa_params["streamlit_filepath"] = os.path.join(
            test_install_config['streamlit_dir'], f"{module_name}.py")
    if test_install_config.get("mcp_dir"):
        paa_params["mcp_module_filepath"] = os.path.join(
            test_install_config['mcp_dir'], f"{module_name}.py")

    if test_install_config.get("artifacts_dir"):
        paa_params["artifacts_dir"] = os.path.join(
            test_install_config["artifacts_dir"], module_name)

    if build_mkdocs:
        paa_params["add_mkdocs_site"] = True

    if test_install_config.get("docs_file_paths"):
        paa_params["docs_file_paths"] = test_install_config.get("docs_file_paths")

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if fastapi_routes_filepath:
        paa_params["fastapi_routes_filepath"] = fastapi_routes_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath

    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir

    if default_version:
        paa_params["default_version"] = default_version
    if check_vulnerabilities:
        paa_params["check_vulnerabilities"] = True

    if skip_deps_compat_check:
        paa_params["check_dependencies_compatibility"] = False

    if check_full_deps_compat:
        paa_params["check_full_dependencies_compatibility"] = True
    
    if check_licenses:
        paa_params["check_dependencies_licenses"] = True

    if skip_deps_install:
        paa_params["skip_deps_install"] = True

    if keep_temp_files:
        remove_temp_files = False
    else:
        remove_temp_files = True

    paa = PackageAutoAssembler(
        **paa_params
    )

    if paa.metadata_h.is_metadata_available():

        paa.add_metadata_from_module()
        paa.add_metadata_from_cli_module()
        paa.metadata['version'] = paa.default_version

        paa.prep_setup_dir()
        paa.merge_local_dependacies()

        paa.add_requirements_from_module()
        paa.add_requirements_from_cli_module()
        paa.add_requirements_from_api_route()
        paa.add_requirements_from_streamlit()
        paa.add_requirements_from_mcp()
        if paa_params.get("add_mkdocs_site"):
            paa.add_readme(execute_notebook = False)
            paa.add_extra_docs()
            paa.make_mkdocs_site()
        if checkpoint:
            cp_result = _create_checkpoint_for_run(
                paa=paa,
                module_name=module_name,
                source_event="test-install",
            )
            if cp_result.get("changed"):
                click.echo(
                    f"Checkpoint created at {cp_result.get('commit')} "
                    f"(tag: {cp_result.get('tag')})"
                )
            else:
                click.echo(
                    f"No checkpoint changes detected. "
                    f"Current checkpoint: {cp_result.get('commit')}"
                )
        paa.prepare_artifacts()
        paa.prep_setup_file()
        paa.make_package()
        click.echo(f"Module {module_name.replace('_','-')} prepared as a package.")
        paa.test_install_package(remove_temp_files = remove_temp_files)
        click.echo(f"Module {module_name.replace('_','-')} installed in local environment, overwriting previous version!")

    else:
        paa.logger.info(f"Metadata condition was not fullfield for {module_name.replace('_','-')}")


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--fastapi-routes-filepath', 'fastapi_routes_filepath',  type=str, required=False, help='Path to .py file that routes for fastapi.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--kernel-name', 'kernel_name', type=str, required=False, help='Kernel name.')
@click.option('--python-version', 'python_version', type=str, required=False, help='Python version.')
@click.option('--default-version', 'default_version', type=str, required=False, help='Default version.')
@click.option('--ignore-vulnerabilities-check', 'ignore_vulnerabilities_check', is_flag=True, type=bool, required=False, help='If checked, does not check module dependencies with pip-audit for vulnerabilities.')
@click.option('--skip-deps-compat-check', 'skip_deps_compat_check', is_flag=True, type=bool, required=False, help='If checked, skips dependency compatibility check.')
@click.option('--skip-full-deps-compat-check', 'skip_full_deps_compat_check', is_flag=True, type=bool, required=False, help='If checked, skips full dependency resolver compatibility check.')
@click.option('--ignore-licenses-check', 'ignore_licenses_check', is_flag=True, type=bool, required=False, help='If checked, does not check module licenses for unexpected ones.')
@click.option('--example-notebook-path', 'example_notebook_path', type=str, required=False, help='Path to .ipynb file to be used as README.')
@click.option('--execute-notebook', 'execute_notebook', is_flag=True, type=bool, required=False, help='If checked, executes notebook before turning into README.')
@click.option('--log-filepath', 'log_filepath', type=str, required=False, help='Path to logfile to record version change.')
@click.option('--versions-filepath', 'versions_filepath', type=str, required=False, help='Path to file where latest versions of the packages are recorded.')
@click.option('--no-checkpoint', 'no_checkpoint', is_flag=True, type=bool, required=False, help='If checked, skips checkpoint creation before package build.')
@click.pass_context
def make_package(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        fastapi_routes_filepath,
        dependencies_dir,
        kernel_name,
        python_version,
        default_version,
        ignore_vulnerabilities_check,
        skip_deps_compat_check,
        skip_full_deps_compat_check,
        ignore_licenses_check,
        example_notebook_path,
        execute_notebook,
        log_filepath,
        versions_filepath,
        no_checkpoint):
    """Package with package-auto-assembler."""

    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    resolved_module_dir = test_install_config.get(
        "module_dir", PAA_PATH_DEFAULTS.get("module_dir", "python_modules")
    )
    resolved_use_commit_messages = test_install_config.get("use_commit_messages", True)

    test_install_config["loggerLvl"] = logging.INFO

    paa_params = {
        "config_filepath" : config,
        "module_name" : f"{module_name}",
        "module_filepath" : os.path.join(resolved_module_dir, f"{module_name}.py"),
        #"mapping_filepath" : test_install_config.get("mapping_filepath"),
        #"licenses_filepath" : test_install_config.get("licenses_filepath"),
        "dependencies_dir" : test_install_config.get("dependencies_dir"),
        "setup_directory" : f"./{module_name}",
        #"versions_filepath" : test_install_config["versions_filepath"],
        #"log_filepath" : test_install_config["log_filepath"],
        "use_commit_messages" : resolved_use_commit_messages,
        "license_path" : _resolve_package_license_path(test_install_config, module_name),
        "notice_path" : _resolve_package_notice_path(test_install_config, module_name),
        "license_label" : test_install_config.get("license_label", None),
        "license_badge" : test_install_config.get("license_badge"),
        "docs_url" : test_install_config.get("docs_url", None),
        "source_repo_url" : test_install_config.get("source_repo_url", None),
        "source_repo_name" : test_install_config.get("source_repo_name", None),
        "add_artifacts" : test_install_config.get("add_artifacts"),
        "add_mkdocs_site" : test_install_config.get("add_mkdocs_site"),
        "artifacts_filepaths" : test_install_config.get("artifacts_filepaths"),
        "release_notes_filepath" : os.path.join('.paa/release_notes',
                                                            f"{module_name}.md"),
        #"docs_path" : test_install_config.get("docs_dir"),
        "check_vulnerabilities" : test_install_config.get("check_vulnerabilities", True),
        "check_dependencies_compatibility": test_install_config.get("make_package_check_dependencies_compatibility", True),
        "check_full_dependencies_compatibility": test_install_config.get("make_package_check_full_dependencies_compatibility", True),
        "check_dependencies_licenses" : test_install_config.get("check_dependencies_licenses", True)
    }

    if test_install_config.get("extra_docs_dir"):
        paa_params["extra_docs_dir"] = os.path.join(
            test_install_config['extra_docs_dir'], f"{module_name}")

    if test_install_config.get("tests_dir"):
        paa_params["tests_dir"] = os.path.join(
            test_install_config['tests_dir'], f"{module_name}")

    if test_install_config.get("drawio_dir"):
        paa_params["drawio_filepath"] = os.path.join(
            test_install_config['drawio_dir'], f"{module_name}.drawio")

        paa_params["drawio_dir"] = test_install_config["drawio_dir"]

    if test_install_config.get("example_notebooks_path"):
        paa_params["example_notebook_path"] = os.path.join(test_install_config["example_notebooks_path"],
                                                           f"{module_name}.ipynb")

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("python_version"):
        paa_params["python_version"] = test_install_config["python_version"]

    if test_install_config.get("kernel_name"):
        paa_params["kernel_name"] = test_install_config["kernel_name"]

    if test_install_config.get("allowed_licenses"):
        paa_params["allowed_licenses"] = test_install_config["allowed_licenses"]

    if test_install_config.get("cli_dir"):
        paa_params["cli_module_filepath"] = os.path.join(
            test_install_config['cli_dir'], f"{module_name}.py")

    if test_install_config.get("api_routes_dir"):
        paa_params["fastapi_routes_filepath"] = os.path.join(
            test_install_config['api_routes_dir'], f"{module_name}.py")

    if test_install_config.get("streamlit_dir"):
        paa_params["streamlit_filepath"] = os.path.join(
            test_install_config['streamlit_dir'], f"{module_name}.py")
    if test_install_config.get("mcp_dir"):
        paa_params["mcp_module_filepath"] = os.path.join(
            test_install_config['mcp_dir'], f"{module_name}.py")

    if test_install_config.get("artifacts_dir"):
        paa_params["artifacts_dir"] = os.path.join(
            test_install_config["artifacts_dir"], module_name)

    if test_install_config.get("docs_file_paths"):
        paa_params["docs_file_paths"] = test_install_config.get("docs_file_paths")

    if test_install_config.get("license_badge"):
        paa_params["license_badge"] = test_install_config.get("license_badge")

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if fastapi_routes_filepath:
        paa_params["fastapi_routes_filepath"] = fastapi_routes_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath

    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir
    if kernel_name:
        paa_params["kernel_name"] = kernel_name
    if python_version:
        paa_params["python_version"] = python_version
    if default_version:
        paa_params["default_version"] = default_version

    if ignore_vulnerabilities_check:
        paa_params["check_vulnerabilities"] = False

    if skip_deps_compat_check:
        paa_params["check_dependencies_compatibility"] = False

    if skip_full_deps_compat_check:
        paa_params["check_full_dependencies_compatibility"] = False

    if ignore_licenses_check:
        paa_params["check_dependencies_licenses"] = False

    if example_notebook_path:
        paa_params["example_notebook_path"] = example_notebook_path
    
    if log_filepath:
        paa_params["log_filepath"] = log_filepath
    if versions_filepath:
        paa_params["versions_filepath"] = versions_filepath

    paa = PackageAutoAssembler(
        **paa_params
    )

    exported_history_temp_root = None
    try:
        if paa.metadata_h.is_metadata_available():

            paa.add_metadata_from_module()
            paa.add_metadata_from_cli_module()
            paa.add_or_update_version()
            if resolved_use_commit_messages:
                paa.add_or_update_release_notes()
            paa.prep_setup_dir()

            paa.merge_local_dependacies()

            paa.add_requirements_from_module()
            paa.add_requirements_from_cli_module()
            paa.add_requirements_from_api_route()
            paa.add_requirements_from_streamlit()
            paa.add_requirements_from_mcp()
            paa.add_readme(execute_notebook = execute_notebook)
            paa.add_extra_docs()
            paa.make_mkdocs_site()
            if not no_checkpoint:
                cp_result = _create_checkpoint_for_run(
                    paa=paa,
                    module_name=module_name,
                    source_event="make-package",
                )
                if cp_result.get("changed"):
                    click.echo(
                        f"Checkpoint created at {cp_result.get('commit')} "
                        f"(tag: {cp_result.get('tag')})"
                    )
                else:
                    click.echo(
                        f"No checkpoint changes detected. "
                        f"Current checkpoint: {cp_result.get('commit')}"
                    )

            pruned_export = paa.checkpoint_h.export_pruned_history(
                module_name=module_name,
                prune_version="0.0.0",
            )
            if pruned_export:
                exported_history_temp_root = pruned_export.get("temp_root")
                if paa.artifacts_filepaths is None:
                    paa.artifacts_filepaths = {}
                paa.artifacts_filepaths[".paa.tracking/git"] = pruned_export.get("worktree_dir")
                paa.artifacts_filepaths[".paa.tracking/git_repo"] = pruned_export.get("git_repo_dir")

            paa.prepare_artifacts()
            paa.prep_setup_file()
            paa.make_package()
            click.echo(f"Module {module_name.replace('_','-')} prepared as a package.")

        else:
            paa.logger.info(f"Metadata condition was not fullfield for {module_name.replace('_','-')}")
    finally:
        if exported_history_temp_root:
            shutil.rmtree(exported_history_temp_root, ignore_errors=True)

@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.pass_context
def check_vulnerabilities(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        dependencies_dir):
    """Check vulnerabilities of the module."""

    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    resolved_module_dir = test_install_config.get(
        "module_dir", PAA_PATH_DEFAULTS.get("module_dir", "python_modules")
    )
    resolved_cli_dir = test_install_config.get(
        "cli_dir", PAA_PATH_DEFAULTS.get("cli_dir", "cli")
    )
    resolved_dependencies_dir = test_install_config.get(
        "dependencies_dir", PAA_PATH_DEFAULTS.get("dependencies_dir", "python_modules/components")
    )

    test_install_config["loggerLvl"] = logging.INFO

    paa_params = {
        "module_name" : f"{module_name}",
        "module_filepath" : os.path.join(resolved_module_dir, f"{module_name}.py"),
        "cli_module_filepath" : os.path.join(resolved_cli_dir, f"{module_name}.py"),
        #"mapping_filepath" : test_install_config["mapping_filepath"],
        "dependencies_dir" : resolved_dependencies_dir,
        "setup_directory" : f"./{module_name}",
        #"versions_filepath" : test_install_config["versions_filepath"],
        #"log_filepath" : test_install_config["log_filepath"],
        "check_vulnerabilities" : True,
        "add_artifacts" : False
    }

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("python_version"):
        paa_params["python_version"] = test_install_config["python_version"]

    if test_install_config.get("kernel_name"):
        paa_params["kernel_name"] = test_install_config["kernel_name"]

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath
    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir

    paa = PackageAutoAssembler(
        **paa_params
    )

    if paa.metadata_h.is_metadata_available():
        paa.add_metadata_from_module()
        paa.add_metadata_from_cli_module()
    else:
        paa.metadata = {}


    paa.metadata['version'] = paa.default_version
    paa.prep_setup_dir()

    try:
        paa.merge_local_dependacies()

        paa.add_requirements_from_module()
        paa.add_requirements_from_cli_module()
    except Exception as e:
        print("")
    finally:
        shutil.rmtree(paa.setup_directory)

    

@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--license-mapping-filepath', 'licenses_filepath', type=str, required=False, help='Path to .json file that maps license labels to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--skip-normalize-labels', 
              'skip_normalize_labels', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, package license labels are not normalized.')
@click.pass_context
def check_licenses(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        licenses_filepath,
        cli_module_filepath,
        dependencies_dir,
        skip_normalize_labels):
    """Check licenses of the module."""

    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    resolved_module_dir = test_install_config.get(
        "module_dir", PAA_PATH_DEFAULTS.get("module_dir", "python_modules")
    )
    resolved_cli_dir = test_install_config.get(
        "cli_dir", PAA_PATH_DEFAULTS.get("cli_dir", "cli")
    )
    resolved_dependencies_dir = test_install_config.get(
        "dependencies_dir", PAA_PATH_DEFAULTS.get("dependencies_dir", "python_modules/components")
    )

    test_install_config["loggerLvl"] = logging.INFO

    paa_params = {
        "module_name" : f"{module_name}",
        "module_filepath" : os.path.join(resolved_module_dir, f"{module_name}.py"),
        "cli_module_filepath" : os.path.join(resolved_cli_dir, f"{module_name}.py"),
        #"mapping_filepath" : test_install_config["mapping_filepath"],
        #"licenses_filepath" : test_install_config["licenses_filepath"],
        "dependencies_dir" : resolved_dependencies_dir,
        "setup_directory" : f"./{module_name}",
        #"versions_filepath" : test_install_config["versions_filepath"],
        #"log_filepath" : test_install_config["log_filepath"],
        "check_vulnerabilities" : False,
        "check_dependencies_licenses" : True,
        "add_artifacts" : False
    }

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("python_version"):
        paa_params["python_version"] = test_install_config["python_version"]

    if test_install_config.get("kernel_name"):
        paa_params["kernel_name"] = test_install_config["kernel_name"]

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath
    if licenses_filepath:
        paa_params["licenses_filepath"] = licenses_filepath
    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir

    paa = PackageAutoAssembler(
        **paa_params
    )

    if skip_normalize_labels:
        normalize_labels = False
    else:
        normalize_labels = True

    if paa.metadata_h.is_metadata_available():
        paa.add_metadata_from_module()
        paa.add_metadata_from_cli_module()
    else:
        paa.metadata = {}

    paa.metadata['version'] = paa.default_version
    paa.prep_setup_dir()

    try:
        paa.merge_local_dependacies()
        paa.add_requirements_from_module()
        paa.add_requirements_from_cli_module()
    except Exception as e:
        print("")
    finally:
        shutil.rmtree(paa.setup_directory)


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-filepath', 'module_filepath', type=str, required=False, help='Path to .py file to be packaged.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--full', 'full', is_flag=True, type=bool, required=False, help='If checked, runs full dependency resolver compatibility check.')
@click.pass_context
def check_deps_compat(ctx,
        config,
        module_name,
        module_filepath,
        mapping_filepath,
        cli_module_filepath,
        dependencies_dir,
        full):
    """Check compatibility of declared dependency constraints for the module."""

    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    resolved_module_dir = test_install_config.get(
        "module_dir", PAA_PATH_DEFAULTS.get("module_dir", "python_modules")
    )
    resolved_cli_dir = test_install_config.get(
        "cli_dir", PAA_PATH_DEFAULTS.get("cli_dir", "cli")
    )
    resolved_dependencies_dir = test_install_config.get(
        "dependencies_dir", PAA_PATH_DEFAULTS.get("dependencies_dir", "python_modules/components")
    )

    test_install_config["loggerLvl"] = logging.INFO

    paa_params = {
        "module_name" : f"{module_name}",
        "module_filepath" : os.path.join(resolved_module_dir, f"{module_name}.py"),
        "cli_module_filepath" : os.path.join(resolved_cli_dir, f"{module_name}.py"),
        "dependencies_dir" : resolved_dependencies_dir,
        "setup_directory" : f"./{module_name}",
        "check_vulnerabilities" : False,
        "check_dependencies_compatibility" : True,
        "check_full_dependencies_compatibility" : full,
        "check_dependencies_licenses" : False,
        "add_artifacts" : False
    }

    if module_filepath:
        paa_params["module_filepath"] = module_filepath
    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath
    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir

    paa = PackageAutoAssembler(
        **paa_params
    )

    if paa.metadata_h.is_metadata_available():
        paa.add_metadata_from_module()
        paa.add_metadata_from_cli_module()
    else:
        paa.metadata = {}

    paa.metadata['version'] = paa.default_version
    paa.prep_setup_dir()

    try:
        paa.merge_local_dependacies()
        paa.add_requirements_from_module()
        paa.add_requirements_from_cli_module()
    except Exception:
        raise
    else:
        if full:
            click.echo("Dependency compatibility checks passed (static + full resolver).")
        else:
            click.echo("Dependency compatibility checks passed.")
    finally:
        shutil.rmtree(paa.setup_directory)



@click.command()
@click.argument('label_name')
@click.option('--version', type=str, required=False, help='Version of new release.')
@click.option('--notes', type=str, required=False, help='Optional manually provided notes string, where each note is separated by ; and increment type is provide in accordance to paa documentation.')
@click.option('--notes-filepath', 'notes_filepath', type=str, required=False, help='Path to .md wit release notes.')
@click.option('--max-search-depth', 'max_search_depth', type=str, required=False, help='Max search depth in commit history.')
@click.option('--use-pip-latest', 'usepip', is_flag=True, type=bool, required=False, help='If checked, attempts to pull latest version from pip.')
@click.pass_context
def update_release_notes(ctx,
        label_name,
        version,
        notes,
        notes_filepath,
        max_search_depth,
        usepip):
    """Update release notes."""

    label_name = label_name.replace('-','_')

    if notes_filepath is None:
        release_notes_path = "./release_notes"
        notes_filepath = os.path.join(release_notes_path,
                                            f"{label_name}.md")

    if usepip:
        usepip = True
    else:
        usepip = False
    
    rnh_params = {
        'filepath' : notes_filepath,
        'label_name' : label_name,
        'version' : "0.0.1"
    }

    vh_params = {
        'versions_filepath' : '',
        'log_filepath' : '',
        'read_files' : False,
        'default_version' : "0.0.0"
    }

    if max_search_depth:
        rnh_params['max_search_depth'] = max_search_depth

    rnh = ReleaseNotesHandler(
        **rnh_params
    )

    if notes:
        if not notes.startswith('['):
            notes = ' ' + notes

        rnh.commit_messages = [f'[{label_name}]{notes}']
        rnh._filter_commit_messages_by_package()
        rnh._clean_and_split_commit_messages()

    if version is None:

        rnh.extract_version_update()

        version_increment_type = rnh.version_update_label

        version = rnh.extract_latest_version()

        if rnh.version != '0.0.1':
            version = rnh.version
        else:

            vh = VersionHandler(
                **vh_params)

            if version:
                vh.versions[label_name] = version

            vh.increment_version(package_name = label_name,
                                                version = None,
                                                increment_type = version_increment_type,
                                                default_version = version,
                                                save = False,
                                                usepip = usepip)

            version = vh.get_version(package_name=label_name)

    rnh.version = version

    rnh.create_release_note_entry()

    rnh.save_release_notes()
    click.echo(f"Release notes for {label_name} with version {version} were updated!")

@click.command()
@click.option('--tags', 
              multiple=True, 
              required=False, 
              help='Keyword tag filters for the package.')
@click.pass_context
def show_module_list(ctx,
        tags):
    """Shows module list."""

    tags = list(tags)

    if tags == []:
        tags = ['aa-paa-tool']
    # else:
    #     tags.append('aa-paa-tool')

    da = DependenciesAnalyser()

    packages = da.filter_packages_by_tags(tags)
    if packages:
        # Calculate the maximum length of package names for formatting
        max_name_length = max(len(pkg[0]) for pkg in packages) if packages else 0
        max_version_length = max(len(pkg[1]) for pkg in packages) if packages else 0
        
        # Print the header
        header_name = "Package"
        header_version = "Version"
        click.echo(f"{header_name:<{max_name_length}} {header_version:<{max_version_length}}")
        click.echo(f"{'-' * max_name_length} {'-' * max_version_length}")

        # Print each package and its version
        for package, version in packages:
            click.echo(f"{package:<{max_name_length}} {version:<{max_version_length}}")
    else:
        click.echo(f"No packages found matching all tags {tags}")

@click.command()
@click.argument('label_name')
@click.pass_context
def show_module_artifacts(ctx,
        label_name):
    """Shows module artifacts."""

    ah = ArtifactsHandler(
        module_name = label_name.replace('-','_')
    )

    package_artifacts = ah.get_packaged_artifacts()

    if package_artifacts:
        # Print each package and its version
        for artifact, path in package_artifacts.items():
            click.echo(f"{artifact}")
    else:
        click.echo(f"No package artifacts found for {label_name}")


@click.command()
@click.argument('label_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-dir', 'module_dir', type=str, required=False, help='Path to folder with .py file to be packaged.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.pass_context
def show_ref_local_deps(ctx,
        config,
        label_name,
        module_dir,
        dependencies_dir):
    """Shows paths to local dependencies referenced in the module."""

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    resolved_module_dir = test_install_config.get(
        "module_dir", PAA_PATH_DEFAULTS.get("module_dir", "python_modules")
    )

    test_install_config["loggerLvl"] = logging.INFO

    module_name = label_name.replace('-','_')

    if module_dir:
        test_install_config['module_dir'] = module_dir
    if dependencies_dir:
        test_install_config['dependencies_dir'] = dependencies_dir

    ld_params = {
        "main_module_filepath" : os.path.join(module_dir or resolved_module_dir, f"{module_name}.py"),
        "dependencies_dir" : test_install_config.get("dependencies_dir")
    }

    ldh = LocalDependaciesHandler(
        **ld_params

    )

    ref_local_deps = ldh.get_module_deps_path()

    if ref_local_deps:
        # Print each package and its version
        for rld in ref_local_deps:
            click.echo(f"{rld}")


@click.command()
@click.argument('label_name')
# @click.option('--is-cli', 
#               'get_paa_cli_status', 
#               is_flag=True, 
#               type=bool, 
#               required=False, 
#               help='If checked, returns true when cli interface is available.')
@click.option('--keywords', 
              'get_keywords', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns keywords for the package.')
@click.option('--classifiers', 
              'get_classifiers', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns classfiers for the package.')
@click.option('--docstring', 
              'get_docstring', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns docstring of the package.')
@click.option('--author', 
              'get_author', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns author of the package.')
@click.option('--author-email', 
              'get_author_email', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns author email of the package.')
@click.option('--version', 
              'get_version', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns installed version of the package.')
@click.option('--license_label', 
              'get_license_label', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns license label of the package.')
# @click.option('--license', 
#               'get_license', 
#               is_flag=True, 
#               type=bool, 
#               required=False, 
#               help='If checked, returns license of the package.')
@click.option('--pip-version', 
              'get_pip_version', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, returns pip latest version of the package.')
# @click.option('--paa-version', 
#               'get_paa_version', 
#               is_flag=True, 
#               type=bool, 
#               required=False, 
#               help='If checked, returns packaging tool version with which the package was packaged.')
@click.pass_context
def show_module_info(ctx,
        label_name,
        #get_paa_cli_status,
        get_keywords,
        get_classifiers,
        get_docstring,
        get_author,
        get_author_email,
        get_version,
        get_pip_version,
        #get_paa_version,
        get_license_label,
        #get_license
        ):
    """Shows module info."""

    package_mapping = {'PIL': 'Pillow',
                        'bs4': 'beautifulsoup4',
                        'fitz': 'PyMuPDF',
                        'attr': 'attrs',
                        'dotenv': 'python-dotenv',
                        'googleapiclient': 'google-api-python-client',
                        'google_auth_oauthlib': 'google-auth-oauthlib',
                        'sentence_transformers': 'sentence-transformers',
                        'flask': 'Flask',
                        'stdlib_list': 'stdlib-list',
                        'sklearn': 'scikit-learn',
                        'yaml': 'pyyaml',
                        'package_auto_assembler': 'package-auto-assembler',
                        'git': 'gitpython'}

    import_name = [key for key,value in package_mapping.items() \
        if value == label_name]

    if len(import_name)>0:
        import_name = import_name[0]
    else:
        import_name = label_name

    try:
        package = importlib.import_module(import_name.replace('-','_'))
    except ImportError:
        click.echo(f"No package with name {label_name} was installed or mapping does not support it!")

    da = DependenciesAnalyser()

    try:
        package_metadata = da.get_package_metadata(label_name)
    except Exception as e:
        click.echo(f"Failed to extract {label_name} metadata!")
        print(e)

    # get docstring
    try:
        docstring = package.__doc__
    except ImportError:
        docstring = None

    try:
        vh_params = {
        'versions_filepath' : '',
        'log_filepath' : '',
        'read_files' : False,
        'default_version' : "0.0.0"
        }

        vh = VersionHandler(**vh_params)

        latest_version = vh.get_latest_pip_version(label_name)
    except Exception as e:
        latest_version = None

    if not any([get_version, 
                get_pip_version,
                #get_paa_version,
                get_author, 
                get_author_email, 
                get_docstring,
                get_classifiers,
                get_keywords,
                #get_paa_cli_status,
                #get_license,
                get_license_label]):

        

        if package_metadata.get('version'):
            click.echo(f"Installed version: {package_metadata.get('version')}")

        if latest_version:
            click.echo(f"Latest pip version: {latest_version}")
        
        # if package_metadata.get('paa_version'):
        #     click.echo(f"Packaged with PAA version: {package_metadata.get('paa_version')}")
        
        # if package_metadata.get('paa_cli'):
        #     click.echo(f"Is cli interface available: {package_metadata.get('paa_cli')}")

        if package_metadata.get('author'):
            click.echo(f"Author: {package_metadata.get('author')}")

        if package_metadata.get('author_email'):
            click.echo(f"Author-email: {package_metadata.get('author_email'):}")

        if package_metadata.get('keywords'):
            click.echo(f"Keywords: {package_metadata.get('keywords')}")

        if package_metadata.get('license_label'):
            click.echo(f"License: {package_metadata.get('license_label')}")

        if package_metadata.get('classifiers'):
            click.echo(f"Classifiers: {package_metadata.get('classifiers')}")

        if docstring:
            click.echo(docstring)
    
    if get_version:
        click.echo(package_metadata.get('version'))
    if get_pip_version:
        click.echo(latest_version)
    # if get_paa_version:
    #     click.echo(package_metadata.get('paa_version'))
    if get_author:
        click.echo(package_metadata.get('author'))
    if get_author_email:
        click.echo(package_metadata.get('author_email'))
    if get_docstring:
        click.echo(docstring)
    if get_classifiers:
        for cl in package_metadata.get('classifiers'):
            click.echo(f"{cl}")
    if get_keywords:
        for kw in package_metadata.get('keywords'):
            click.echo(f"{kw}")
    # if get_paa_cli_status:
    #     click.echo(package_metadata.get('paa_cli'))
    if get_license_label:
        click.echo(package_metadata.get('license_label'))
    # if get_license:
    #     click.echo(license_text)


@click.command()
@click.argument('label_name')
@click.pass_context
def show_module_requirements(ctx,
        label_name):
    """Shows module requirements."""

    da = DependenciesAnalyser()

    label_name = label_name.replace('-','_')
    requirements = da.get_package_requirements(label_name)
    
    for req in requirements:
        click.echo(f"{req}")

@click.command()
@click.argument('package_name')
@click.option('--normalize-labels', 
              'normalize_labels', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, package license labels are normalized.')
@click.pass_context
def show_module_licenses(ctx,
        package_name,
        normalize_labels):
    """Shows module licenses."""

    da = DependenciesAnalyser(loggerLvl = logging.INFO)
    
    package_name = package_name.replace('-','_')

    if normalize_labels:
        normalize_labels = True
    else:
        normalize_labels = False
    

    extracted_dependencies_tree = da.extract_dependencies_tree(
        package_name = package_name
    )

    extracted_dependencies_tree_license = da.add_license_labels_to_dep_tree(
        dependencies_tree = extracted_dependencies_tree,
        normalize = normalize_labels
    )

    da.print_flattened_tree(extracted_dependencies_tree_license)

@click.command()
@click.option('--api-config','api_config', type=str, 
             default=".paa.api.config",
             required=False, 
             help='Path to yml config file with app description, middleware parameters, run parameters, `.paa.api.config` is used by default.')
@click.option('--host', default=None, help='The host to bind to.')
@click.option('--port', default=None, help='The port to bind to.')
@click.option('--package', 
              'package_names',
              multiple=True,
              required=False, 
              help='Package names from which routes will be added to the app.')
@click.option('--route', 
              'routes_paths', 
              multiple=True, 
              required=False, 
              help='Paths to routes which will be added to the app.')
@click.option('--docs', 
              'docs_paths', 
              multiple=True, 
              required=False, 
              help='Paths to static docs site which will be added to the app.')
@click.pass_context
def run_api_routes(ctx,
        api_config,
        package_names,
        routes_paths,
        docs_paths,
        host,
        port):
    """Run fastapi with provided routes."""

    if os.path.exists(api_config):
        with open(api_config, 'r') as file:
            api_config = yaml.safe_load(file)
    else:
        api_config = {}

    description_config = api_config.get('DESCRIPTION')
    middleware_config = api_config.get('MIDDLEWARE')
    run_config = api_config.get('RUN')

    if run_config is None:
        run_config = {}

    if host:
        run_config['host'] = host

    if port:
        run_config['port'] = port
    

    fah = FastApiHandler(loggerLvl = logging.INFO)
    
    fah.run_app(
        description = description_config,
        middleware = middleware_config,
        run_parameters = run_config,
        package_names = package_names,
        routes_paths = routes_paths,
        docs_paths = docs_paths
    )

@click.command()
@click.option('--app-config','app_config', type=str, 
             default=".paa.streamlit.config",
             required=False, 
             help='Path to yml config for streamlit app.')
@click.option('--host', default=None, help='The host to bind to.')
@click.option('--port', default=None, help='The port to bind to.')
@click.option('--package', 
              'package_name',
              required=False, 
              help='Package name from which streamlit app should be run.')
@click.option('--path', 
              'streamlit_filepath',
              required=False, 
              help='Path to streamlit app.')
@click.pass_context
def run_streamlit(ctx,
        app_config,
        package_name,
        streamlit_filepath,
        host,
        port):
    """Run streamlit application from the package."""


    sh = StreamlitHandler(loggerLvl = logging.INFO)
    
    sh.run_app(
        package_name = package_name,
        streamlit_filepath = streamlit_filepath,
        config_path = app_config,
        host = host,
        port = port
    )


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, default=".paa.config", show_default=True, help='Path to config file for paa.')
@click.option('--force', 'force', is_flag=True, type=bool, required=False, help='If checked, overwrite existing MCP module.')
@click.pass_context
def init_mcp(ctx,
        module_name,
        config,
        force):
    """Create MCP module scaffold for a package in PPR."""

    module_name = module_name.replace("-", "_")
    config_data = _load_effective_paa_paths(config)
    mcp_dir = config_data.get("mcp_dir", PAA_PATH_DEFAULTS.get("mcp_dir", "mcp"))
    os.makedirs(mcp_dir, exist_ok=True)

    mcp_filepath = os.path.join(mcp_dir, f"{module_name}.py")
    if os.path.exists(mcp_filepath) and (not force):
        click.echo(f"{mcp_filepath} already exists. Use --force to overwrite.")
        return

    with open(mcp_filepath, "w", encoding="utf-8") as file:
        file.write(_render_mcp_template(module_name))

    click.echo(f"MCP scaffold created: {mcp_filepath}")


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, default=".paa.config", show_default=True, help='Path to config file for paa.')
@click.option('--force', 'force', is_flag=True, type=bool, required=False, help='If checked, overwrite existing api routes module.')
@click.pass_context
def init_api(ctx,
        module_name,
        config,
        force):
    """Create API routes scaffold for a package in PPR."""

    module_name = module_name.replace("-", "_")

    config_data = {}
    if os.path.exists(config):
        with open(config, 'r', encoding='utf-8') as file:
            loaded = yaml.safe_load(file) or {}
            if isinstance(loaded, dict):
                config_data = loaded

    api_routes_dir = config_data.get("api_routes_dir") or test_install_config.get("api_routes_dir") or "api_routes"
    api_filepath = os.path.join(api_routes_dir, f"{module_name}.py")

    os.makedirs(api_routes_dir, exist_ok=True)

    if os.path.exists(api_filepath) and not force:
        click.echo(f"{api_filepath} already exists. Use --force to overwrite.")
        return

    with open(api_filepath, "w", encoding="utf-8") as file:
        file.write(_render_api_routes_template(module_name))

    click.echo(f"API routes scaffold created: {api_filepath}")


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, default=".paa.config", show_default=True, help='Path to config file for paa.')
@click.option('--force', 'force', is_flag=True, type=bool, required=False, help='If checked, overwrite existing cli module.')
@click.pass_context
def init_cli(ctx,
        module_name,
        config,
        force):
    """Create CLI scaffold for a package in PPR."""

    module_name = module_name.replace("-", "_")

    config_data = {}
    if os.path.exists(config):
        with open(config, 'r', encoding='utf-8') as file:
            loaded = yaml.safe_load(file) or {}
            if isinstance(loaded, dict):
                config_data = loaded

    cli_dir = config_data.get("cli_dir") or test_install_config.get("cli_dir") or "cli"
    cli_filepath = os.path.join(cli_dir, f"{module_name}.py")

    os.makedirs(cli_dir, exist_ok=True)

    if os.path.exists(cli_filepath) and not force:
        click.echo(f"{cli_filepath} already exists. Use --force to overwrite.")
        return

    with open(cli_filepath, "w", encoding="utf-8") as file:
        file.write(_render_cli_template(module_name))

    click.echo(f"CLI scaffold created: {cli_filepath}")


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, default=".paa.config", show_default=True, help='Path to config file for paa.')
@click.option('--force', 'force', is_flag=True, type=bool, required=False, help='If checked, overwrite existing streamlit module.')
@click.pass_context
def init_streamlit(ctx,
        module_name,
        config,
        force):
    """Create Streamlit scaffold for a package in PPR."""

    module_name = module_name.replace("-", "_")

    config_data = {}
    if os.path.exists(config):
        with open(config, 'r', encoding='utf-8') as file:
            loaded = yaml.safe_load(file) or {}
            if isinstance(loaded, dict):
                config_data = loaded

    streamlit_dir = config_data.get("streamlit_dir") or test_install_config.get("streamlit_dir") or "streamlit"
    streamlit_filepath = os.path.join(streamlit_dir, f"{module_name}.py")

    os.makedirs(streamlit_dir, exist_ok=True)

    if os.path.exists(streamlit_filepath) and not force:
        click.echo(f"{streamlit_filepath} already exists. Use --force to overwrite.")
        return

    with open(streamlit_filepath, "w", encoding="utf-8") as file:
        file.write(_render_streamlit_template(module_name))

    click.echo(f"Streamlit scaffold created: {streamlit_filepath}")


@click.command()
@click.argument('module_name')
@click.option('--target',
              'target',
              type=click.Choice(['codex', 'claude'], case_sensitive=False),
              required=False,
              help='Agent target for MCP registration.')
@click.option('--config', type=str, required=False, default=".paa.config", show_default=True, help='Path to config file for paa.')
@click.option('--python-path',
              'python_path',
              type=str,
              required=False,
              default=sys.executable,
              show_default=True,
              help='Python interpreter to run MCP module with.')
@click.option('--server-name',
              'server_name',
              type=str,
              required=False,
              help='Optional MCP server name override.')
@click.pass_context
def add_mcp(ctx,
        module_name,
        target,
        config,
        python_path,
        server_name):
    """Register package MCP module in codex/claude client."""

    module_name = module_name.replace("-", "_")
    effective_target = _detect_agent_target(target)
    mcp_filepath = _resolve_installed_mcp_module_path(module_name)

    if mcp_filepath is None:
        raise click.ClickException(
            f"No installed MCP module found for '{module_name}'. "
            f"Run `paa test-install {module_name.replace('_', '-')}` (or install that package) first."
        )

    if server_name is None:
        server_name = f"{module_name.replace('_', '-')}-mcp"

    _register_mcp_server_for_agent(
        target=effective_target,
        server_name=server_name,
        python_path=python_path,
        module_path=os.path.abspath(mcp_filepath),
    )
    click.echo(
        f"Registered MCP server '{server_name}' for target '{effective_target}' "
        f"using {os.path.abspath(mcp_filepath)}"
    )


@click.command()
@click.argument('label_name')
@click.pass_context
def show_module_mcp(ctx,
        label_name):
    """Show MCP module availability and registered tool list for an installed package."""

    module_name = label_name.replace("-", "_")
    try:
        package = importlib.import_module(module_name)
    except ImportError:
        click.echo(f"No package with name {label_name} was installed!")
        return

    package_dir = os.path.dirname(package.__file__)
    mcp_filepath = os.path.join(package_dir, "mcp_server.py")

    if os.path.exists(mcp_filepath):
        click.echo(f"MCP module available: {mcp_filepath}")
        try:
            spec = importlib.util.spec_from_file_location(f"{module_name}_mcp_server", mcp_filepath)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Could not load MCP module spec from {mcp_filepath}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[attr-defined]

            mcp_server = getattr(module, "mcp", None)
            if mcp_server is None:
                click.echo("No FastMCP server object named `mcp` found.")
                return

            tool_names = []
            tool_manager = getattr(mcp_server, "_tool_manager", None)
            if tool_manager is not None and hasattr(tool_manager, "list_tools"):
                tools = tool_manager.list_tools()
                tool_names = sorted(
                    [getattr(tool, "name", None) for tool in tools if getattr(tool, "name", None)]
                )

            if tool_names:
                click.echo("MCP tools:")
                for tool_name in tool_names:
                    click.echo(f"- {tool_name}")
            else:
                click.echo("No MCP tools found in module registry.")
        except Exception as exc:
            click.echo(f"Failed to inspect MCP tools: {exc}")
    else:
        click.echo(f"No MCP module found in installed package {label_name}.")


@click.command()
@click.option('--mcp-config',
              'mcp_config',
              type=str,
              default=".paa.mcp.config",
              required=False,
              help='Path to yml config file with MCP run settings and sources.')
@click.option('--package',
              'package_names',
              multiple=True,
              required=False,
              help='Package names from which MCP app should be run.')
@click.option('--path',
              'mcp_filepaths',
              multiple=True,
              required=False,
              help='Path(s) to MCP module file.')
@click.option('--host',
              'host',
              required=False,
              help='Host to bind MCP server to.')
@click.option('--port',
              'port',
              required=False,
              type=int,
              help='Port to bind MCP server to.')
@click.option('--transport',
              'transport',
              required=False,
              type=click.Choice(['sse', 'streamable-http'], case_sensitive=False),
              help='Hosted MCP transport mode.')
@click.option('--mount-path',
              'mount_path',
              required=False,
              default=None,
              help='Optional mount path for SSE transport.')
@click.option('--mode',
              'mode',
              required=False,
              type=click.Choice(['split', 'combine'], case_sensitive=False),
              help='Run mode for MCP hosting.')
@click.option('--server-prefix',
              'server_prefix',
              required=False,
              default=None,
              help='Server name prefix. In split mode used only when explicitly provided.')
@click.pass_context
def run_mcp(ctx,
        mcp_config,
        package_names,
        mcp_filepaths,
        host,
        port,
        transport,
        mount_path,
        mode,
        server_prefix):
    """Run hosted MCP application(s) from package(s) and/or filepath(s)."""

    config_data = {}
    if mcp_config and os.path.exists(mcp_config):
        with open(mcp_config, 'r', encoding='utf-8') as file:
            loaded = yaml.safe_load(file) or {}
            if isinstance(loaded, dict):
                config_data = loaded

    run_cfg = config_data.get("RUN") if isinstance(config_data.get("RUN"), dict) else {}
    src_cfg = config_data.get("SOURCES") if isinstance(config_data.get("SOURCES"), dict) else {}

    cfg_packages = src_cfg.get("packages") or []
    cfg_paths = src_cfg.get("paths") or []
    if isinstance(cfg_packages, str):
        cfg_packages = [cfg_packages]
    if isinstance(cfg_paths, str):
        cfg_paths = [cfg_paths]

    cli_packages = list(package_names or [])
    cli_paths = list(mcp_filepaths or [])

    effective_packages = cli_packages if cli_packages else list(cfg_packages)
    effective_paths = cli_paths if cli_paths else list(cfg_paths)

    if (not effective_packages) and (not effective_paths):
        raise click.ClickException(
            "Provide MCP sources via --package/--path or .paa.mcp.config SOURCES."
        )

    effective_mode = (mode or run_cfg.get("mode") or "split").lower()
    effective_transport = (transport or run_cfg.get("transport") or "streamable-http").lower()
    effective_host = host or run_cfg.get("host") or "127.0.0.1"
    effective_port = int(port if port is not None else (run_cfg.get("port") or 8000))
    effective_mount_path = mount_path if mount_path is not None else run_cfg.get("mount_path")

    # In split mode prefix is applied only when explicitly provided.
    if server_prefix is not None:
        effective_server_prefix = server_prefix
    else:
        if effective_mode == "combine":
            effective_server_prefix = run_cfg.get("server_prefix") or "paa-http"
        else:
            effective_server_prefix = run_cfg.get("server_prefix")

    click.echo(
        "MCP run resolved: "
        f"mode={effective_mode}, transport={effective_transport}, host={effective_host}, "
        f"port={effective_port}, server_prefix={effective_server_prefix}"
    )
    click.echo(f"MCP sources packages={effective_packages} paths={effective_paths}")

    mcp_h = McpHandler(loggerLvl=logging.INFO)
    mcp_h.run_apps(
        package_names=effective_packages,
        mcp_filepaths=effective_paths,
        host=effective_host,
        port=effective_port,
        transport=effective_transport,
        mount_path=effective_mount_path,
        mode=effective_mode,
        server_prefix=effective_server_prefix
    )

@click.command()
@click.argument('package_name')
@click.option('--output-dir', 
              'output_dir', 
              type=str, required=False, 
              help='Directory where routes extracted from the package will be copied to.')
@click.option('--output-path', 
              'output_path', 
              type=str, required=False, 
              help='Filepath to which routes extracted from the package will be copied to.')
@click.pass_context
def extract_module_routes(ctx,
        package_name,
        output_dir,
        output_path):
    """Extracts routes for fastapi from packages that have them into a file."""

    fah = FastApiHandler(loggerLvl = logging.INFO)

    fah.extract_routes_from_package(
        package_name = package_name.replace("-", "_"), 
        output_directory = output_dir, 
        output_filepath = output_path
    )

@click.command()
@click.argument('package_name')
@click.option('--output-dir', 
              'output_dir', 
              type=str, required=False, 
              help='Directory where streamplit extracted from the package will be copied to.')
@click.option('--output-path', 
              'output_path', 
              type=str, required=False, 
              help='Filepath to which streamlit extracted from the package will be copied to.')
@click.pass_context
def extract_module_streamlit(ctx,
        package_name,
        output_dir,
        output_path):
    """Extracts streamlit from packages that have them into a file."""

    sh = StreamlitHandler(loggerLvl = logging.INFO)

    sh.extract_streamlit_from_package(
        package_name = package_name.replace("-", "_"), 
        output_directory = output_dir, 
        output_filepath = output_path
    )


@click.command()
@click.argument('package_name')
@click.option('--output-dir',
              'output_dir',
              type=str, required=False,
              help='Directory where MCP module extracted from the package will be copied to.')
@click.option('--output-path',
              'output_path',
              type=str, required=False,
              help='Filepath to which MCP module extracted from the package will be copied to.')
@click.pass_context
def extract_module_mcp(ctx,
        package_name,
        output_dir,
        output_path):
    """Extract MCP module from packages that have it into a file."""

    mcp_h = McpHandler(loggerLvl=logging.INFO)
    mcp_h.extract_mcp_from_package(
        package_name = package_name.replace("-", "_"),
        output_directory = output_dir,
        output_filepath = output_path
    )

@click.command()
@click.argument('package_name')
@click.option('--artifact', 
              type=str, required=False, 
              help='Name of the artifact to be extracted.')
@click.option('--output-dir', 
              'output_dir', 
              type=str, required=False, 
              help='Directory where artifacts extracted from the package will be copied to.')
@click.option('--output-path', 
              'output_path', 
              type=str, required=False, 
              help='Filepath to which artifact extracted from the package will be copied to.')
@click.pass_context
def extract_module_artifacts(ctx,
        package_name,
        artifact,
        output_dir,
        output_path):
    """Extracts artifacts from packaged module."""

    ah = ArtifactsHandler(
        module_name = package_name.replace('-','_')
    )

    package_artifacts = ah.get_packaged_artifacts()


    if artifact:

        if output_dir is None:
            output_dir = '.'

        if output_path is None:
            output_path = os.path.join(output_dir, artifact)

        if artifact in package_artifacts.keys():
            shutil.copy(package_artifacts[artifact], output_path)
        else:
            click.echo(f"Artifact {artifact} was not found in {package_name}!")
    else:

        destination = 'artifacts'

        if output_dir:
            destination = output_dir
        if output_path:
            destination = output_path

        with pkg_resources.path(f"{package_name.replace('-','_')}", 
            'artifacts') as path:
                artifacts_filepath = path

        if os.path.exists(artifacts_filepath):
            shutil.copytree(artifacts_filepath, destination)
        else:
            click.echo(f"Artifacts were not found in {package_name}!")

@click.command()
@click.argument('package_name')
@click.option('--output-dir', 
              'output_dir', 
              type=str, required=False, 
              help='Directory where routes extracted from the package will be copied to.')
@click.option('--output-path', 
              'output_path', 
              type=str, required=False, 
              help='Filepath to which routes extracted from the package will be copied to.')
@click.pass_context
def extract_module_site(ctx,
        package_name,
        output_dir,
        output_path):
    """Extracts static mkdocs site from packaged module."""

    destination = 'mkdocs'

    if output_dir:
        destination = output_dir
    if output_path:
        destination = output_path

    with pkg_resources.path(f"{package_name.replace('-','_')}", 
            'mkdocs') as path:
                mkdocs_filepath = path

    if os.path.exists(mkdocs_filepath):
        shutil.copytree(mkdocs_filepath, destination)
    else:
        click.echo(f"Mkdocs static page was not found in {package_name}!")


@click.command()
@click.argument('package_name')
@click.option('--format',
              'output_format',
              type=click.Choice(['pep621', 'uv', 'poetry'], case_sensitive=False),
              default='pep621',
              show_default=True,
              help='Output format for extracted pyproject.')
@click.option('--output-dir',
              'output_dir',
              type=str,
              required=False,
              help='Directory where extracted pyproject will be copied/generated.')
@click.option('--output-path',
              'output_path',
              type=str,
              required=False,
              help='Filepath where extracted pyproject will be copied/generated.')
@click.pass_context
def extract_module_pyproject(ctx,
        package_name,
        output_format,
        output_dir,
        output_path):
    """Extracts package pyproject metadata from installed package tracking."""

    module_name = package_name.replace('-', '_')
    package_root = pkg_resources.files(module_name)
    tracked_pyproject = os.path.join(package_root, ".paa.tracking", "pyproject.toml")

    if output_path is None:
        if output_dir is None:
            output_dir = "."
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "pyproject.toml")
    else:
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

    fmt = output_format.lower()

    if fmt in ("pep621", "uv"):
        if not os.path.exists(tracked_pyproject):
            click.echo(f"Tracked pyproject was not found in installed package {package_name}!")
            return

        shutil.copy(tracked_pyproject, output_path)
        click.echo(f"Extracted {fmt} pyproject to {output_path}")
        return

    da = DependenciesAnalyser()
    package_metadata = da.get_package_metadata(package_name=package_name)
    requirements = da.get_package_requirements(package_name=package_name)

    poetry_content = _render_poetry_pyproject(
        package_name=module_name,
        package_metadata=package_metadata,
        requirements=requirements
    )
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(poetry_content)

    click.echo(f"Generated poetry pyproject to {output_path}")

@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--module-dir', 'module_dir', type=str, required=False, help='Path to folder where module is stored.')
@click.option('--mapping-filepath', 'mapping_filepath', type=str, required=False, help='Path to .json file that maps import to install dependecy names.')
@click.option('--cli-module-filepath', 'cli_module_filepath',  type=str, required=False, help='Path to .py file that contains cli logic.')
@click.option('--routes-module-filepath', 'routes_module_filepath',  type=str, required=False, help='Path to .py file that contains fastapi routes.')
@click.option('--streamlit-module-filepath', 'streamlit_module_filepath',  type=str, required=False, help='Path to .py file that contains streamlit app.')
@click.option('--dependencies-dir', 'dependencies_dir', type=str, required=False, help='Path to directory with local dependencies of the module.')
@click.option('--show-extra', 
              'show_extra', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, list will show which requirements are extra.')
@click.option('--skip-extra', 
              'skip_extra', 
              is_flag=True, 
              type=bool, 
              required=False, 
              help='If checked, list will not include extra.')
@click.pass_context
def extract_module_requirements(ctx,
        config,
        module_name,
        module_dir,
        mapping_filepath,
        cli_module_filepath,
        routes_module_filepath,
        streamlit_module_filepath,
        dependencies_dir,
        show_extra,
        skip_extra):
    """Extract module requirements."""

    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    test_install_config["loggerLvl"] = logging.INFO

    paa_params = {
        "module_name" : f"{module_name}",
        "setup_directory" : f"./{module_name}",
        "check_vulnerabilities" : False,
        "add_artifacts" : False
    }

    if test_install_config.get("module_dir"):
        paa_params["module_filepath"] = os.path.join(test_install_config['module_dir'], f"{module_name}.py")

    if test_install_config.get("dependencies_dir"):
        paa_params["dependencies_dir"] = test_install_config["dependencies_dir"]

    if test_install_config.get("default_version"):
        paa_params["default_version"] = test_install_config["default_version"]

    if test_install_config.get("classifiers"):
        paa_params["classifiers"] = test_install_config["classifiers"]

    if test_install_config.get("python_version"):
        paa_params["python_version"] = test_install_config["python_version"]

    if test_install_config.get("kernel_name"):
        paa_params["kernel_name"] = test_install_config["kernel_name"]

    if test_install_config.get("cli_dir"):
        paa_params["cli_module_filepath"] = os.path.join(test_install_config.get("cli_dir"), f"{module_name}.py")
    if test_install_config.get("api_routes_dir"):
        paa_params["fastapi_routes_filepath"] = os.path.join(test_install_config.get("api_routes_dir"), f"{module_name}.py")
    if test_install_config.get("streamlit_dir"):
        paa_params["streamlit_filepath"] = os.path.join(test_install_config.get("streamlit_dir"), f"{module_name}.py")
    if test_install_config.get("mcp_dir"):
        paa_params["mcp_module_filepath"] = os.path.join(test_install_config.get("mcp_dir"), f"{module_name}.py")

    if cli_module_filepath:
        paa_params["cli_module_filepath"] = cli_module_filepath
    if routes_module_filepath:
        paa_params["fastapi_routes_filepath"] = routes_module_filepath
    if streamlit_module_filepath:
        paa_params["streamlit_filepath"] = streamlit_module_filepath
    if mapping_filepath:
        paa_params["mapping_filepath"] = mapping_filepath
    if dependencies_dir:
        paa_params["dependencies_dir"] = dependencies_dir

    if module_dir:
        paa_params["module_filepath"] = os.path.join(module_dir, f"{module_name}.py")


    paa = PackageAutoAssembler(
        **paa_params
    )

    paa.metadata = {}

    paa.metadata['version'] = paa.default_version
    paa.prep_setup_dir()

    try:
        paa.merge_local_dependacies()
        paa.add_requirements_from_module()
        paa.add_requirements_from_cli_module()
        paa.add_requirements_from_api_route()
        paa.add_requirements_from_streamlit()
        paa.add_requirements_from_mcp()

        if skip_extra:
            opt_req = []
        else:

            if show_extra:

                opt_req = [r + "; extra == 'all'" for r in paa.optional_requirements_list]
            else:
                opt_req = paa.optional_requirements_list



        requirements_list = paa.requirements_list + opt_req

        for req in requirements_list:
            click.echo(req)

    except Exception as e:
        print("")
    finally:
        shutil.rmtree(paa.setup_directory)



@click.command()
@click.argument('label_name')
@click.pass_context
def show_module_artifact_links(ctx,
        label_name):
    """Shows module artifact links."""

    ah = ArtifactsHandler(
        module_name = label_name.replace('-','_'))

    link_for_artifacts, link_availability = ah.show_module_links()

    if link_for_artifacts:

        artifact_names = [a.replace(".link","") for a,l in link_for_artifacts.items()]
        artifact_links = [l for a,l in  link_for_artifacts.items()]
        link_availabilities = [la for a,la in  link_availability.items()]

        # Calculate the maximum length of package names for formatting
        max_name_length = max(len(a) for a in artifact_names) if artifact_names else 0
        max_link_length = max(len(l) for l in artifact_links) if artifact_links else 0
        max_link_a_length = max(len(str(la)) for la in link_availabilities) if link_availabilities else 0
        
        # Print the header
        header_name = "Artifact"
        header_link = "Link"
        header_availability = "Available"

        click.echo(f"{header_name:<{max_name_length}} {header_link:<{max_link_length}} {header_availability:<{max_link_a_length}}")
        click.echo(f"{'-' * max_name_length} {'-' * max_link_length} {'-' * max_link_a_length}")

        # Print each package and its version
        for artifact, link in link_for_artifacts.items():
            available = link_availability[artifact]
            artifact = artifact.replace(".link","")
            click.echo(f"{artifact:<{max_name_length}} {link:<{max_link_length}} {str(available):<{max_link_a_length}}")
    
    else:
        click.echo(f"No link for package artifacts found for {label_name}!")

@click.command()
@click.argument('label_name')
@click.pass_context
def refresh_module_artifacts(ctx,
        label_name):
    """Refreshes module artifact from links."""

    ah = ArtifactsHandler(
        module_name = label_name.replace('-','_'))

    failed_refreshes = ah.refresh_artifacts_from_link()

    link_for_artifacts, _ = ah.show_module_links()

    click.echo(f"{len(link_for_artifacts) - failed_refreshes} links refreshed for {label_name}")


@click.command()
@click.argument('module_name')
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.pass_context
def extract_tracking_version(ctx,
        config,
        module_name):
    """Get latest package version."""


    module_name = module_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    test_install_config = {}
    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    MAPPING_FILE = ".paa/tracking/lsts_package_versions.yml"#test_install_config['mapping_filepath']
    VERSIONS_FILE = ".paa/tracking/version_logs.csv" #test_install_config['versions_filepath']

    module_version = "0.0.0"
    if os.path.exists(VERSIONS_FILE):

        with open(MAPPING_FILE, 'r') as file:
            # Load the contents of the file
            mapping_file = yaml.safe_load(file) or {}

        module_version = mapping_file.get(
            module_name, 
            test_install_config.get("default_version", "0.0.0"))
    
    click.echo(module_version)
    
@click.command()
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--label-name', 'label_name', type=str, required=False, help='Label name.')
@click.option('--drawio-dir', 'drawio_dir', type=str, required=False, help='Path to a directory where drawio files are stored.')
@click.option('--docs-dir', 'docs_dir', type=str, required=False, help='Path to the output directory for .png file.')
@click.pass_context
def convert_drawio_to_png(ctx,
        config,
        label_name,
        drawio_dir,
        docs_dir):
    """Converts drawio file to .png"""

    module_name = None
    if label_name:
        module_name = label_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    test_install_config = {}
    if os.path.exists(config):
        with open(config, 'r', encoding='utf-8') as file:
            test_install_config_up = yaml.safe_load(file) or {}
        test_install_config.update(test_install_config_up)

    resolved_drawio_dir = drawio_dir or test_install_config.get(
        "drawio_dir",
        PAA_PATH_DEFAULTS.get("drawio_dir", "drawio")
    )
    resolved_docs_dir = docs_dir or os.path.join(
        test_install_config.get("paa_dir", ".paa"),
        "docs"
    )

    paa_params = {
        "module_filepath" : "",
        "module_name" : "",
        "drawio_dir" : resolved_drawio_dir,
        "docs_path": resolved_docs_dir
    }

    paa_h = PackageAutoAssembler(
        **paa_params
    )

    paa_h._initialize_ppr_h(params={
        "paa_dir": paa_h.paa_dir,
        "drawio_dir": resolved_drawio_dir,
        "docs_dir": resolved_docs_dir,
        "module_dir": paa_h.module_dir,
        "pylint_threshold": paa_h.pylint_threshold,
        "logger": paa_h.logger
    })

    status = paa_h.ppr_h.convert_drawio_to_png(module_name = module_name)
    
    if status > 1:
        click.echo("Path to convert_drawio_to_png.sh not found within packaged artifacts!")

    if status > 0:
        click.echo("Path to package-auto-assembler package not found!")

@click.command()
@click.option('--config', type=str, required=False, help='Path to config file for paa.')
@click.option('--label-name', 'label_name', type=str, required=False, help='Label name.')
@click.option('--module-dir', 'module_dir', type=str, required=False, help='Path to a directory where .py files are stored.')
@click.option('--threshold', 'threshold', type=str, required=False, help='Pylint threshold.')
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.pass_context
def run_pylint_tests(ctx,
        config,
        label_name,
        module_dir,
        threshold,
        files):
    """Run pylint tests for a given module, file, files or files in a directory."""


    module_name = None
    if label_name:
        module_name = label_name.replace('-','_')

    if config is None:
        config = ".paa.config"

    test_install_config = {}
    if os.path.exists(config):
        with open(config, 'r') as file:
            test_install_config_up = yaml.safe_load(file)

        test_install_config.update(test_install_config_up)

    resolved_module_dir = test_install_config.get(
        "module_dir", PAA_PATH_DEFAULTS.get("module_dir", "python_modules")
    )
    resolved_dependencies_dir = test_install_config.get(
        "dependencies_dir", PAA_PATH_DEFAULTS.get("dependencies_dir", "python_modules/components")
    )

    paa_params = {
        "module_filepath" : "",
        "module_name" : "",
        "module_dir" : resolved_module_dir,
        "pylint_threshold" : test_install_config.get("pylint_threshold")

    }

    if module_dir:
        paa_params["module_dir"] = module_dir

    if threshold:
        paa_params["pylint_threshold"] = threshold


    files_to_check = []
    if files:
        files_to_check = files
    else:

        if module_name:

            ld_params = {
                "main_module_filepath" : os.path.join(
                    module_dir or resolved_module_dir,
                    f"{module_name}.py"
                ),
                "dependencies_dir" : resolved_dependencies_dir
            }

            ldh = LocalDependaciesHandler(
                **ld_params)
                
            files_to_check = ldh.get_module_deps_path()


    paa_h = PackageAutoAssembler(
        **paa_params
    )

    paa_h._initialize_ppr_h(params={
        "paa_dir": paa_h.paa_dir,
        "drawio_dir": paa_h.drawio_dir,
        "docs_dir": paa_h.docs_path,
        "module_dir": module_dir or resolved_module_dir,
        "pylint_threshold": threshold or test_install_config.get("pylint_threshold"),
        "logger": paa_h.logger
    })

    status = paa_h.ppr_h.run_pylint_tests(files_to_check = files_to_check)
    
    if status > 1:
        click.echo("Path to pylint_test.sh not found within packaged artifacts!")

    if status > 0:
        click.echo("Path to package-auto-assembler package not found!")


cli.add_command(init_paa, "init-paa")
cli.add_command(init_config, "init-config")
cli.add_command(init_mcp_config, "init-mcp-config")
cli.add_command(init_api_config, "init-api-config")
cli.add_command(init_streamlit_config, "init-streamlit-config")
cli.add_command(init_ppr, "init-ppr")
cli.add_command(unfold_package, "unfold-package")
cli.add_command(remove_package, "remove-package")
cli.add_command(rename_package, "rename-package")
cli.add_command(test_install, "test-install")
cli.add_command(make_package, "make-package")
cli.add_command(check_vulnerabilities, "check-vulnerabilities")
cli.add_command(check_licenses, "check-licenses")
cli.add_command(check_deps_compat, "check-deps-compat")
cli.add_command(update_release_notes, "update-release-notes")
cli.add_command(run_api_routes, "run-api-routes")
cli.add_command(run_streamlit, "run-streamlit")
cli.add_command(run_mcp, "run-mcp")
cli.add_command(run_pylint_tests, "run-pylint-tests")
cli.add_command(init_mcp, "init-mcp")
cli.add_command(init_api, "init-api")
cli.add_command(init_cli, "init-cli")
cli.add_command(init_streamlit, "init-streamlit")
cli.add_command(add_mcp, "add-mcp")
cli.add_command(show_module_list, "show-module-list")
cli.add_command(show_module_info, "show-module-info")
cli.add_command(show_module_mcp, "show-module-mcp")
cli.add_command(show_module_requirements, "show-module-requirements")
cli.add_command(show_module_licenses, "show-module-licenses")
cli.add_command(show_module_artifacts, "show-module-artifacts")
cli.add_command(show_module_artifact_links, "show-module-artifacts-links")
cli.add_command(show_ref_local_deps, "show-ref-local-deps")
cli.add_command(refresh_module_artifacts, "refresh-module-artifacts")
cli.add_command(extract_tracking_version, "extract-tracking-version")
cli.add_command(extract_module_routes, "extract-module-routes")
cli.add_command(extract_module_streamlit, "extract-module-streamlit")
cli.add_command(extract_module_mcp, "extract-module-mcp")
cli.add_command(extract_module_artifacts, "extract-module-artifacts")
cli.add_command(extract_module_requirements, "extract-module-requirements")
cli.add_command(extract_module_site, "extract-module-site")
cli.add_command(extract_module_pyproject, "extract-module-pyproject")
cli.add_command(extract_skill, "extract-skill")
cli.add_command(extract_skills, "extract-skills")
cli.add_command(cleanup_agent_skills, "cleanup-agent-skills")
cli.add_command(checkpoint_create, "checkpoint-create")
cli.add_command(checkpoint_prune, "checkpoint-prune")
cli.add_command(checkpoint_list, "checkpoint-list")
cli.add_command(checkpoint_show, "checkpoint-show")
cli.add_command(checkout, "checkout")
cli.add_command(convert_drawio_to_png, "convert-drawio-to-png")


if __name__ == "__main__":
    cli()
