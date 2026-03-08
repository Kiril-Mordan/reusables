"""
MCP server for package-auto-assembler.

This module exposes read-only inspection tools similar to CLI show commands.
"""

import os
import sys
import subprocess
import importlib
import importlib.util
import importlib.metadata
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from package_auto_assembler import (
    DependenciesAnalyser,
    ArtifactsHandler,
    CheckpointHandler,
    LocalDependaciesHandler,
    PAA_PATH_DEFAULTS,
)


mcp = FastMCP("package-auto-assembler")


@mcp.tool()
def show_module_list(tags: list[str] | None = None) -> list[dict[str, str]]:
    """
    Return installed PAA module list filtered by tags.
    """

    if not tags:
        tags = ["aa-paa-tool"]

    da = DependenciesAnalyser()
    packages = da.filter_packages_by_tags(tags)
    return [{"package": package, "version": version} for package, version in packages]


@mcp.tool()
def show_module_info(label_name: str) -> dict[str, Any]:
    """
    Return key metadata for an installed package.
    """

    module_name = label_name.replace("-", "_")
    da = DependenciesAnalyser()

    try:
        package = importlib.import_module(module_name)
    except ImportError:
        return {"ok": False, "error": f"Package '{label_name}' is not installed."}

    try:
        metadata = da.get_package_metadata(label_name)
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"Failed to load metadata for '{label_name}': {exc}"}

    installed_version = None
    try:
        installed_version = importlib.metadata.version(label_name)
    except importlib.metadata.PackageNotFoundError:
        installed_version = None

    return {
        "ok": True,
        "name": label_name,
        "import_name": module_name,
        "installed_version": installed_version,
        "docstring": package.__doc__,
        "metadata": metadata,
    }


@mcp.tool()
def show_module_requirements(label_name: str) -> dict[str, Any]:
    """
    Return package requirements.
    """

    da = DependenciesAnalyser()
    try:
        requirements = da.get_package_requirements(package_name=label_name)
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"Failed to extract requirements for '{label_name}': {exc}"}

    return {"ok": True, "requirements": requirements}


@mcp.tool()
def show_module_artifacts(label_name: str) -> dict[str, Any]:
    """
    Return packaged artifacts for an installed package.
    """

    module_name = label_name.replace("-", "_")
    ah = ArtifactsHandler(module_name=module_name)
    try:
        artifacts = ah.get_packaged_artifacts()
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"Failed to read artifacts for '{label_name}': {exc}"}

    return {"ok": True, "artifacts": sorted(list(artifacts.keys()))}


@mcp.tool()
def show_module_artifact_links(label_name: str) -> dict[str, Any]:
    """
    Return packaged artifact links and availability.
    """

    module_name = label_name.replace("-", "_")
    ah = ArtifactsHandler(module_name=module_name)
    try:
        links, availability = ah.show_module_links()
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"Failed to read artifact links for '{label_name}': {exc}"}

    items = []
    for artifact, link in sorted(links.items()):
        items.append({
            "artifact": artifact.replace(".link", ""),
            "link": link,
            "available": bool(availability.get(artifact, False)),
        })

    return {"ok": True, "links": items}


@mcp.tool()
def show_module_licenses(label_name: str, normalize_labels: bool = False) -> dict[str, Any]:
    """
    Return flattened dependency->license mapping for an installed package.
    """

    module_name = label_name.replace("-", "_")
    da = DependenciesAnalyser()
    try:
        dep_tree = da.extract_dependencies_tree(package_name=module_name)
        dep_licenses = da.add_license_labels_to_dep_tree(
            dependencies_tree=dep_tree,
            normalize=normalize_labels
        )
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"Failed to extract licenses for '{label_name}': {exc}"}

    return {"ok": True, "licenses": dep_licenses}


@mcp.tool()
def list_package_skills(package_name: str) -> dict[str, Any]:
    """
    Return skill names available in installed package.
    """
    module_name = package_name.replace("-", "_")

    try:
        package_root = _resolve_installed_package_root(module_name=module_name)
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"Failed to resolve installed package '{package_name}': {exc}"}

    candidates = [
        package_root / ".paa.tracking" / "skills" / module_name,
        package_root / ".paa.tracking" / "skills",
        package_root / "skills" / module_name,
        package_root / "skills",
    ]

    skills_root = None
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            skills_root = candidate
            break

    if skills_root is None:
        return {"ok": False, "error": f"No installed skills directory found for '{package_name}'."}

    skills = []
    for path in sorted(skills_root.iterdir(), key=lambda p: p.name.lower()):
        if path.is_dir() and (path / "SKILL.md").exists():
            skills.append(path.name)

    return {
        "ok": True,
        "package_name": package_name,
        "module_name": module_name,
        "skills_root": str(skills_root),
        "skills": skills,
    }


def _resolve_installed_package_root(module_name: str = "package_auto_assembler") -> Path:
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise FileNotFoundError(f"Cannot resolve installed module '{module_name}'")

    if spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations)))

    if spec.origin:
        return Path(spec.origin).parent

    raise FileNotFoundError(f"Cannot resolve root for '{module_name}'")


@mcp.tool()
def run_pylint_test(
    package_name: str | None = None,
    module_dir: str | None = None,
    files_to_check: list[str] | None = None,
    threshold: float | None = None,
) -> dict[str, Any]:
    """
    Run pylint test script bundled in installed package-auto-assembler.
    """

    module_root = Path(module_dir).resolve() if module_dir else Path.cwd().resolve()
    files_to_check = list(files_to_check or [])

    try:
        package_root = _resolve_installed_package_root()
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"Failed to resolve installed package_auto_assembler: {exc}"}

    script_path = package_root / "artifacts" / "tools" / "pylint_test.sh"
    if not script_path.exists():
        return {"ok": False, "error": f"pylint_test.sh not found at {script_path}"}

    if package_name and not files_to_check:
        module_name = package_name.replace("-", "_")
        candidate_dirs = [
            Path.cwd() / "python_modules",
            Path.cwd(),
        ]

        main_module_filepath = None
        resolved_module_dir = None
        for candidate_dir in candidate_dirs:
            candidate_main = candidate_dir / f"{module_name}.py"
            if candidate_main.exists():
                main_module_filepath = candidate_main
                resolved_module_dir = candidate_dir
                break

        if main_module_filepath is None:
            return {
                "ok": False,
                "error": (
                    f"Could not resolve local module file for '{package_name}'. "
                    "Provide files_to_check or run from PPR root."
                ),
            }

        ldh = LocalDependaciesHandler(
            main_module_filepath=str(main_module_filepath),
            dependencies_dir=str((resolved_module_dir / "components").resolve()),
        )
        files_to_check = ldh.get_module_deps_path()
        files_to_check = [str(Path(path).resolve()) for path in files_to_check]
        module_root = Path(resolved_module_dir).resolve()

    command = [str(script_path), "--module-directory", str(module_root)]
    if threshold is not None:
        command.extend(["--threshold", str(threshold)])
    if files_to_check:
        command.extend(files_to_check)

    result = subprocess.run(command, capture_output=True, text=True, check=False)

    return {
        "ok": result.returncode == 0,
        "return_code": result.returncode,
        "command": command,
        "module_dir": str(module_root),
        "files_to_check": files_to_check,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _checkpoint_handler() -> CheckpointHandler:
    return CheckpointHandler(
        path_defaults=dict(PAA_PATH_DEFAULTS),
        get_module_deps_paths=(
            lambda main_module_filepath, dependencies_dir: LocalDependaciesHandler(
                main_module_filepath=main_module_filepath,
                dependencies_dir=dependencies_dir,
            ).get_module_deps_path()
        ),
    )


@mcp.tool()
def checkpoint_list(module_name: str, limit: int = 20) -> dict[str, Any]:
    """
    Return checkpoint list for module from packaged/unfolded history.
    """

    ch = _checkpoint_handler()
    try:
        checkpoints = ch.list_checkpoints(module_name=module_name, limit=limit)
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"Failed to list checkpoints for '{module_name}': {exc}"}

    return {"ok": True, "checkpoints": checkpoints}


@mcp.tool()
def checkpoint_show(module_name: str, target: str = "latest") -> dict[str, Any]:
    """
    Return details for one checkpoint target (tag/commit/latest).
    """

    ch = _checkpoint_handler()
    try:
        info = ch.show_checkpoint(module_name=module_name, target=target)
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"Failed to show checkpoint for '{module_name}': {exc}"}

    return {"ok": True, "checkpoint": info}


if __name__ == "__main__":
    mcp.run()
