import os
import re
import shutil
import subprocess
import tempfile
import importlib.resources as pkg_resources
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import attrs
import attrsx
import yaml

# pylint: disable=missing-function-docstring,too-many-lines,unsubscriptable-object,not-callable

@attrsx.define
class CheckpointHandler:
    """
    Maintains per-package git-based checkpoint history in an internal store.
    """

    paa_config_path = attrs.field(default=".paa.config")
    history_root = attrs.field(default=".paa/history")
    git_user_name = attrs.field(default="PAA Checkpoint")
    git_user_email = attrs.field(default="paa@local")

    # Injected from main class / CLI.
    path_defaults = attrs.field(
        type=dict,
        factory=lambda: {
            "module_dir": "python_modules",
            "dependencies_dir": "python_modules/components",
            "example_notebooks_path": "example_notebooks",
            "cli_dir": "cli",
            "api_routes_dir": "api_routes",
            "streamlit_dir": "streamlit",
            "artifacts_dir": "artifacts",
            "drawio_dir": "drawio",
            "extra_docs_dir": "extra_docs",
            "tests_dir": "tests",
            "licenses_dir": "licenses",
        }
    )
    get_module_deps_paths = attrs.field(default=None, type=Optional[Callable])

    def _normalize_module_name(self, module_name: str) -> str:
        return module_name.replace("-", "_")

    def _load_effective_config(self) -> dict:
        config = dict(self.path_defaults)
        config_path = Path(self.paa_config_path)
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as file:
                loaded = yaml.safe_load(file) or {}
            for key, value in loaded.items():
                if value is not None:
                    config[key] = value
        return config

    def _module_history_git_dir(self, module_name: str) -> Path:
        module_name = self._normalize_module_name(module_name)
        return Path(self.history_root) / module_name / "git"

    def _installed_history_git_dir(self, module_name: str):
        module_name = self._normalize_module_name(module_name)
        try:
            package_root = Path(pkg_resources.files(module_name))
        except (ModuleNotFoundError, TypeError, AttributeError):
            return None

        git_dir = package_root / ".paa.tracking" / "git"
        if (git_dir / ".git").exists():
            return git_dir
        return None

    def _installed_history_context(self, module_name: str):
        module_name = self._normalize_module_name(module_name)
        try:
            package_root = Path(pkg_resources.files(module_name))
        except (ModuleNotFoundError, TypeError, AttributeError):
            return None

        work_tree = package_root / ".paa.tracking" / "git"
        if (work_tree / ".git").exists():
            return {"cwd": work_tree, "git_dir": None, "work_tree": None}

        git_repo = package_root / ".paa.tracking" / "git_repo"
        if git_repo.exists() and work_tree.exists():
            return {
                "cwd": package_root / ".paa.tracking",
                "git_dir": git_repo,
                "work_tree": work_tree,
            }
        return None

    def _history_context_for_read(self, module_name: str):
        module_name = self._normalize_module_name(module_name)
        installed_ctx = self._installed_history_context(module_name)
        if installed_ctx is not None:
            return installed_ctx
        return {"cwd": self._module_history_git_dir(module_name), "git_dir": None, "work_tree": None}

    def _run_git(
        self,
        args: list,
        cwd: Path,
        check: bool = True,
        git_dir: Path = None,
        work_tree: Path = None,
    ):
        cmd = ["git"]
        if git_dir is not None:
            cmd.append(f"--git-dir={str(git_dir)}")
        if work_tree is not None:
            cmd.append(f"--work-tree={str(work_tree)}")
        cmd += args
        result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
        if check and result.returncode != 0:
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            raise RuntimeError(
                f"Git command failed: {' '.join(cmd)}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            )
        return result

    def _parse_semver_tag(self, tag: str):
        match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag.strip())
        if not match:
            return None
        return tuple(int(part) for part in match.groups())

    def init_history_repo(self, module_name: str) -> Path:
        module_name = self._normalize_module_name(module_name)
        git_dir = self._module_history_git_dir(module_name)
        git_dir.mkdir(parents=True, exist_ok=True)

        if not (git_dir / ".git").exists():
            self._run_git(["init"], cwd=git_dir)
            self._run_git(["config", "user.name", self.git_user_name], cwd=git_dir)
            self._run_git(["config", "user.email", self.git_user_email], cwd=git_dir)

        return git_dir

    def _copy_file_if_exists(self, src: Path, dst: Path):
        if src.exists() and src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def _copy_dir_if_exists(self, src: Path, dst: Path):
        if src.exists() and src.is_dir():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    def _resolve_dependency_paths(self, main_module_src: Path, dependencies_dir: Path) -> list:
        if (self.get_module_deps_paths is None) or (not callable(self.get_module_deps_paths)):
            return []

        dep_paths = self.get_module_deps_paths(
            main_module_filepath=str(main_module_src),
            dependencies_dir=str(dependencies_dir),
        )
        if not dep_paths:
            return []
        # Caller may return main module as first path; keep only dependency files.
        return [Path(dep) for dep in dep_paths if Path(dep) != main_module_src]

    def _is_notebook_generated_png(self, filename: str, module_name: str) -> bool:
        is_new_pattern = filename.startswith(f"{module_name}_ipynb_cell") and filename.endswith(".png")
        is_legacy_pattern = filename.startswith(f"{module_name}_cell") and "_out" in filename and filename.endswith(".png")
        return is_new_pattern or is_legacy_pattern

    def _is_package_docs_entry(self, entry_name: str, module_name: str) -> bool:
        if entry_name == f"{module_name}.md":
            return True
        if entry_name.startswith(f"{module_name}-"):
            return True
        if self._is_notebook_generated_png(entry_name, module_name):
            return True
        return False

    def build_canonical_tree(self, module_name: str, paa_config: dict = None) -> Path:
        module_name = self._normalize_module_name(module_name)
        config = paa_config or self._load_effective_config()

        tmp_root = Path(tempfile.mkdtemp(prefix=f"paa_checkpoint_{module_name}_"))

        module_dir = Path(config.get("module_dir", self.path_defaults["module_dir"]))
        dependencies_dir = Path(config.get("dependencies_dir", self.path_defaults["dependencies_dir"]))
        cli_dir = Path(config.get("cli_dir", self.path_defaults["cli_dir"]))
        api_routes_dir = Path(config.get("api_routes_dir", self.path_defaults["api_routes_dir"]))
        streamlit_dir = Path(config.get("streamlit_dir", self.path_defaults["streamlit_dir"]))
        notebooks_dir = Path(config.get("example_notebooks_path", self.path_defaults["example_notebooks_path"]))
        drawio_dir = Path(config.get("drawio_dir", self.path_defaults["drawio_dir"]))
        tests_dir = Path(config.get("tests_dir", self.path_defaults["tests_dir"]))
        artifacts_dir = Path(config.get("artifacts_dir", self.path_defaults["artifacts_dir"]))
        extra_docs_dir = Path(config.get("extra_docs_dir", self.path_defaults["extra_docs_dir"]))
        licenses_dir = Path(config.get("licenses_dir", self.path_defaults["licenses_dir"]))
        skills_dir = Path("skills")
        docs_dir = Path(".paa/docs")

        main_module_src = module_dir / f"{module_name}.py"
        self._copy_file_if_exists(main_module_src, tmp_root / "module" / f"{module_name}.py")
        self._copy_file_if_exists(cli_dir / f"{module_name}.py", tmp_root / "cli" / f"{module_name}.py")
        self._copy_file_if_exists(api_routes_dir / f"{module_name}.py", tmp_root / "api_routes" / f"{module_name}.py")
        self._copy_file_if_exists(streamlit_dir / f"{module_name}.py", tmp_root / "streamlit" / f"{module_name}.py")
        self._copy_file_if_exists(notebooks_dir / f"{module_name}.ipynb", tmp_root / "example_notebooks" / f"{module_name}.ipynb")
        self._copy_file_if_exists(drawio_dir / f"{module_name}.drawio", tmp_root / "drawio" / f"{module_name}.drawio")
        self._copy_file_if_exists(Path(".paa/release_notes") / f"{module_name}.md", tmp_root / "tracking" / "release_notes.md")
        self._copy_file_if_exists(Path(".paa/pyproject") / f"{module_name}.toml", tmp_root / "tracking" / "pyproject.toml")
        self._copy_file_if_exists(licenses_dir / module_name / "LICENSE", tmp_root / "licenses" / "LICENSE")
        self._copy_file_if_exists(licenses_dir / module_name / "NOTICE", tmp_root / "licenses" / "NOTICE")

        if main_module_src.exists() and dependencies_dir.exists():
            for dep in self._resolve_dependency_paths(main_module_src, dependencies_dir):
                if dep.exists() and dep.is_file():
                    try:
                        rel = dep.relative_to(dependencies_dir)
                    except ValueError:
                        rel = Path(dep.name)
                    self._copy_file_if_exists(dep, tmp_root / "dependencies" / rel)

        self._copy_dir_if_exists(tests_dir / module_name, tmp_root / "tests" / module_name)
        self._copy_dir_if_exists(artifacts_dir / module_name, tmp_root / "artifacts" / module_name)
        self._copy_dir_if_exists(extra_docs_dir / module_name, tmp_root / "extra_docs" / module_name)
        self._copy_dir_if_exists(skills_dir / module_name, tmp_root / "skills" / module_name)
        if docs_dir.exists() and docs_dir.is_dir():
            for entry_name in os.listdir(docs_dir):
                if not self._is_package_docs_entry(entry_name=entry_name, module_name=module_name):
                    continue
                source_path = docs_dir / entry_name
                target_path = tmp_root / "docs_cache" / entry_name
                if source_path.is_dir():
                    self._copy_dir_if_exists(source_path, target_path)
                elif source_path.is_file():
                    self._copy_file_if_exists(source_path, target_path)

        return tmp_root

    def _sync_canonical_to_repo(self, canonical_root: Path, git_dir: Path):
        for entry in git_dir.iterdir():
            if entry.name == ".git":
                continue
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()

        for entry in canonical_root.iterdir():
            dst = git_dir / entry.name
            if entry.is_dir():
                shutil.copytree(entry, dst)
            else:
                shutil.copy2(entry, dst)

    def _staged_changes_exist(self, git_dir: Path) -> bool:
        self._run_git(["add", "-A"], cwd=git_dir)
        result = self._run_git(["diff", "--cached", "--quiet"], cwd=git_dir, check=False)
        if result.returncode == 0:
            return False
        if result.returncode == 1:
            return True
        stderr = (result.stderr or "").strip()
        raise RuntimeError(f"Failed to detect staged changes: {stderr}")

    def _head_commit(self, git_dir: Path) -> str:
        result = self._run_git(["rev-parse", "HEAD"], cwd=git_dir, check=False)
        if result.returncode != 0:
            return None
        return (result.stdout or "").strip() or None

    def _apply_checkpoint_tags(self, git_dir: Path, version_label: str):
        if version_label == "0.0.0":
            self._run_git(["tag", "-f", "dev-latest"], cwd=git_dir)
            return "dev-latest"

        tag = f"v{version_label}"
        exists = self._run_git(["tag", "--list", tag], cwd=git_dir)
        if not (exists.stdout or "").strip():
            self._run_git(["tag", tag], cwd=git_dir)
        return tag

    def create_checkpoint(
        self,
        module_name: str,
        version_label: str = "0.0.0",
        source_event: str = "manual",
        paa_config: dict = None,
    ) -> dict:
        module_name = self._normalize_module_name(module_name)
        git_dir = self.init_history_repo(module_name)
        canonical_root = self.build_canonical_tree(module_name=module_name, paa_config=paa_config)

        try:
            self._sync_canonical_to_repo(canonical_root=canonical_root, git_dir=git_dir)
            changed = self._staged_changes_exist(git_dir=git_dir)

            if changed:
                timestamp = datetime.now(timezone.utc).isoformat()
                msg = f"checkpoint[{source_event}] version={version_label} ts={timestamp}"
                self._run_git(["commit", "-m", msg], cwd=git_dir)
                commit = self._head_commit(git_dir=git_dir)
                tag = self._apply_checkpoint_tags(git_dir=git_dir, version_label=version_label)
                return {
                    "module_name": module_name,
                    "changed": True,
                    "commit": commit,
                    "tag": tag,
                    "history_repo": str(git_dir),
                }

            return {
                "module_name": module_name,
                "changed": False,
                "commit": self._head_commit(git_dir=git_dir),
                "tag": None,
                "history_repo": str(git_dir),
            }
        finally:
            shutil.rmtree(canonical_root, ignore_errors=True)

    def list_checkpoints(self, module_name: str, limit: int = 50) -> list:
        module_name = self._normalize_module_name(module_name)
        git_ctx = self._history_context_for_read(module_name)
        has_repo = (Path(git_ctx["cwd"]) / ".git").exists() or (
            git_ctx.get("git_dir") is not None and Path(git_ctx.get("git_dir")).exists()
        )
        if not has_repo:
            return []

        tags_raw = self._run_git(
            ["show-ref", "--tags"],
            cwd=git_ctx["cwd"],
            check=False,
            git_dir=git_ctx.get("git_dir"),
            work_tree=git_ctx.get("work_tree"),
        )
        commit_tags = {}
        if tags_raw.returncode == 0:
            for line in (tags_raw.stdout or "").splitlines():
                if not line.strip():
                    continue
                commit, ref = line.split(" ", 1)
                tag = ref.rsplit("/", 1)[-1]
                commit_tags.setdefault(commit, []).append(tag)

        log = self._run_git(
            ["log", f"--max-count={limit}", "--pretty=format:%H|%cI|%s"],
            cwd=git_ctx["cwd"],
            check=False,
            git_dir=git_ctx.get("git_dir"),
            work_tree=git_ctx.get("work_tree"),
        )
        if log.returncode != 0:
            return []

        checkpoints = []
        for line in (log.stdout or "").splitlines():
            if not line.strip():
                continue
            commit, committed_at, message = line.split("|", 2)
            checkpoints.append(
                {
                    "commit": commit,
                    "committed_at": committed_at,
                    "message": message,
                    "tags": sorted(commit_tags.get(commit, [])),
                }
            )

        return checkpoints

    def _resolve_checkpoint_target(self, git_ctx: dict, target: str) -> str:
        if target in (None, ""):
            tags_raw = self._run_git(
                ["tag", "--list"],
                cwd=git_ctx["cwd"],
                check=False,
                git_dir=git_ctx.get("git_dir"),
                work_tree=git_ctx.get("work_tree"),
            )
            if tags_raw.returncode == 0:
                semver_tags = []
                for raw in (tags_raw.stdout or "").splitlines():
                    tag = raw.strip()
                    parsed = self._parse_semver_tag(tag)
                    if parsed is not None:
                        semver_tags.append((parsed, tag))
                if semver_tags:
                    semver_tags.sort(key=lambda item: item[0], reverse=True)
                    return semver_tags[0][1]
            raise ValueError(
                "No stable checkpoint tags (vX.Y.Z) found. "
                "Provide explicit target like 'dev-latest' or commit hash."
            )
        if target == "latest":
            return "HEAD"
        return target

    # pylint: disable=too-many-return-statements,too-many-branches
    def _canonical_path_to_repo_path(self, module_name: str, config: dict, canonical_path: str):
        canonical = Path(canonical_path)
        if not canonical.parts:
            return None

        module_name = self._normalize_module_name(module_name)
        root = canonical.parts[0]

        if root == "module" and len(canonical.parts) == 2:
            return Path(config.get("module_dir", self.path_defaults["module_dir"])) / canonical.parts[1]
        if root == "dependencies":
            rel = Path(*canonical.parts[1:])
            return Path(config.get("dependencies_dir", self.path_defaults["dependencies_dir"])) / rel
        if root == "cli" and len(canonical.parts) == 2:
            return Path(config.get("cli_dir", self.path_defaults["cli_dir"])) / canonical.parts[1]
        if root == "api_routes" and len(canonical.parts) == 2:
            return Path(config.get("api_routes_dir", self.path_defaults["api_routes_dir"])) / canonical.parts[1]
        if root == "streamlit" and len(canonical.parts) == 2:
            return Path(config.get("streamlit_dir", self.path_defaults["streamlit_dir"])) / canonical.parts[1]
        if root == "example_notebooks" and len(canonical.parts) == 2:
            return Path(config.get("example_notebooks_path", self.path_defaults["example_notebooks_path"])) / canonical.parts[1]
        if root == "drawio" and len(canonical.parts) == 2:
            return Path(config.get("drawio_dir", self.path_defaults["drawio_dir"])) / canonical.parts[1]
        if root == "tracking" and len(canonical.parts) == 2:
            if canonical.parts[1] == "release_notes.md":
                return Path(".paa/release_notes") / f"{module_name}.md"
            if canonical.parts[1] == "pyproject.toml":
                return Path(".paa/pyproject") / f"{module_name}.toml"
        if root == "licenses" and len(canonical.parts) == 2:
            return Path(config.get("licenses_dir", self.path_defaults["licenses_dir"])) / module_name / canonical.parts[1]
        if root == "tests" and len(canonical.parts) >= 2:
            rel = Path(*canonical.parts[1:])
            return Path(config.get("tests_dir", self.path_defaults["tests_dir"])) / rel
        if root == "artifacts" and len(canonical.parts) >= 2:
            rel = Path(*canonical.parts[1:])
            return Path(config.get("artifacts_dir", self.path_defaults["artifacts_dir"])) / rel
        if root == "extra_docs" and len(canonical.parts) >= 2:
            rel = Path(*canonical.parts[1:])
            return Path(config.get("extra_docs_dir", self.path_defaults["extra_docs_dir"])) / rel
        if root == "skills" and len(canonical.parts) >= 2:
            rel = Path(*canonical.parts[1:])
            return Path("skills") / rel
        if root == "docs_cache" and len(canonical.parts) >= 2:
            rel = Path(*canonical.parts[1:])
            return Path(".paa/docs") / rel

        return None

    def _target_tree_files(self, git_ctx: dict, target_commit: str) -> list:
        ls = self._run_git(
            ["ls-tree", "-r", "--name-only", target_commit],
            cwd=git_ctx["cwd"],
            git_dir=git_ctx.get("git_dir"),
            work_tree=git_ctx.get("work_tree"),
        )
        return [line.strip() for line in (ls.stdout or "").splitlines() if line.strip()]

    def _target_file_bytes(self, git_ctx: dict, target_commit: str, canonical_path: str) -> bytes:
        cmd = ["git"]
        if git_ctx.get("git_dir") is not None:
            cmd.append(f"--git-dir={str(git_ctx.get('git_dir'))}")
        if git_ctx.get("work_tree") is not None:
            cmd.append(f"--work-tree={str(git_ctx.get('work_tree'))}")
        cmd += ["show", f"{target_commit}:{canonical_path}"]
        blob = subprocess.run(cmd, cwd=str(git_ctx["cwd"]), capture_output=True, text=False, check=False)
        if blob.returncode != 0:
            return b""
        return blob.stdout or b""

    # pylint: disable=too-many-branches
    def _collect_current_scoped_files(self, module_name: str, config: dict) -> set:
        module_name = self._normalize_module_name(module_name)
        scoped = set()

        direct_files = [
            Path(config.get("module_dir", self.path_defaults["module_dir"])) / f"{module_name}.py",
            Path(config.get("cli_dir", self.path_defaults["cli_dir"])) / f"{module_name}.py",
            Path(config.get("api_routes_dir", self.path_defaults["api_routes_dir"])) / f"{module_name}.py",
            Path(config.get("streamlit_dir", self.path_defaults["streamlit_dir"])) / f"{module_name}.py",
            Path(config.get("example_notebooks_path", self.path_defaults["example_notebooks_path"])) / f"{module_name}.ipynb",
            Path(config.get("drawio_dir", self.path_defaults["drawio_dir"])) / f"{module_name}.drawio",
            Path(".paa/release_notes") / f"{module_name}.md",
            Path(".paa/pyproject") / f"{module_name}.toml",
            Path(config.get("licenses_dir", self.path_defaults["licenses_dir"])) / module_name / "LICENSE",
            Path(config.get("licenses_dir", self.path_defaults["licenses_dir"])) / module_name / "NOTICE",
        ]
        for path in direct_files:
            if path.exists() and path.is_file():
                scoped.add(str(path))

        dir_roots = [
            Path(config.get("tests_dir", self.path_defaults["tests_dir"])) / module_name,
            Path(config.get("artifacts_dir", self.path_defaults["artifacts_dir"])) / module_name,
            Path(config.get("extra_docs_dir", self.path_defaults["extra_docs_dir"])) / module_name,
            Path("skills") / module_name,
        ]
        for root in dir_roots:
            if root.exists() and root.is_dir():
                for file in root.rglob("*"):
                    if file.is_file():
                        scoped.add(str(file))

        docs_dir = Path(".paa/docs")
        if docs_dir.exists() and docs_dir.is_dir():
            for entry_name in os.listdir(docs_dir):
                if not self._is_package_docs_entry(entry_name=entry_name, module_name=module_name):
                    continue
                entry_path = docs_dir / entry_name
                if entry_path.is_file():
                    scoped.add(str(entry_path))
                elif entry_path.is_dir():
                    for file in entry_path.rglob("*"):
                        if file.is_file():
                            scoped.add(str(file))

        return scoped

    def show_checkout_plan(
        self,
        module_name: str,
        target: str = None,
        unfold: bool = False,
        no_install: bool = False,
        keep_temp_files: bool = False,
        paa_config: dict = None,
    ) -> dict:
        module_name = self._normalize_module_name(module_name)
        config = paa_config or self._load_effective_config()
        git_ctx = self._history_context_for_read(module_name)
        has_repo = (Path(git_ctx["cwd"]) / ".git").exists() or (
            git_ctx.get("git_dir") is not None and Path(git_ctx.get("git_dir")).exists()
        )
        if not has_repo:
            raise FileNotFoundError(f"No checkpoint history found for '{module_name}'.")

        target_ref = self._resolve_checkpoint_target(git_ctx=git_ctx, target=target)
        commit_resolve = self._run_git(
            ["rev-parse", target_ref],
            cwd=git_ctx["cwd"],
            check=False,
            git_dir=git_ctx.get("git_dir"),
            work_tree=git_ctx.get("work_tree"),
        )
        if commit_resolve.returncode != 0:
            raise ValueError(f"Could not resolve checkout target '{target_ref}' for '{module_name}'.")
        target_commit = (commit_resolve.stdout or "").strip()

        files_to_write = []
        files_to_update = []
        files_to_delete = []

        target_files = self._target_tree_files(git_ctx=git_ctx, target_commit=target_commit)
        mapped_target_paths = set()

        if unfold:
            for canonical_path in target_files:
                repo_path = self._canonical_path_to_repo_path(
                    module_name=module_name,
                    config=config,
                    canonical_path=canonical_path,
                )
                if repo_path is None:
                    continue

                repo_path_str = str(repo_path)
                mapped_target_paths.add(repo_path_str)

                if not repo_path.exists():
                    files_to_write.append(repo_path_str)
                    continue

                try:
                    current_bytes = repo_path.read_bytes()
                    target_bytes = self._target_file_bytes(
                        git_ctx=git_ctx,
                        target_commit=target_commit,
                        canonical_path=canonical_path,
                    )
                except OSError:
                    files_to_update.append(repo_path_str)
                    continue

                if current_bytes != target_bytes:
                    files_to_update.append(repo_path_str)

            current_scoped = self._collect_current_scoped_files(module_name=module_name, config=config)
            for current_path in sorted(current_scoped):
                if current_path not in mapped_target_paths:
                    files_to_delete.append(current_path)

        return {
            "module_name": module_name,
            "target_input": target,
            "resolved_target": target_ref,
            "target_commit": target_commit,
            "would_create_temp_workspace": True,
            "would_unfold_sync": bool(unfold),
            "would_install": not bool(no_install),
            "would_cleanup_temp": not bool(keep_temp_files),
            "files_to_write": sorted(files_to_write),
            "files_to_update": sorted(files_to_update),
            "files_to_delete": sorted(files_to_delete),
        }

    def apply_checkpoint_to_workspace(
        self,
        module_name: str,
        target: str = None,
        workspace_root: str = ".",
        delete_missing: bool = True,
        paa_config: dict = None,
    ) -> dict:
        module_name = self._normalize_module_name(module_name)
        config = paa_config or self._load_effective_config()
        git_ctx = self._history_context_for_read(module_name)
        has_repo = (Path(git_ctx["cwd"]) / ".git").exists() or (
            git_ctx.get("git_dir") is not None and Path(git_ctx.get("git_dir")).exists()
        )
        if not has_repo:
            raise FileNotFoundError(f"No checkpoint history found for '{module_name}'.")

        target_ref = self._resolve_checkpoint_target(git_ctx=git_ctx, target=target)
        commit_resolve = self._run_git(
            ["rev-parse", target_ref],
            cwd=git_ctx["cwd"],
            check=False,
            git_dir=git_ctx.get("git_dir"),
            work_tree=git_ctx.get("work_tree"),
        )
        if commit_resolve.returncode != 0:
            raise ValueError(f"Could not resolve checkout target '{target_ref}' for '{module_name}'.")
        target_commit = (commit_resolve.stdout or "").strip()

        workspace_root_path = Path(workspace_root).resolve()
        workspace_root_path.mkdir(parents=True, exist_ok=True)

        target_files = self._target_tree_files(git_ctx=git_ctx, target_commit=target_commit)
        mapped_target_paths = set()
        written = 0
        updated = 0

        for canonical_path in target_files:
            repo_rel_path = self._canonical_path_to_repo_path(
                module_name=module_name,
                config=config,
                canonical_path=canonical_path,
            )
            if repo_rel_path is None:
                continue

            dest_path = workspace_root_path / repo_rel_path
            mapped_target_paths.add(str(dest_path))

            target_bytes = self._target_file_bytes(
                git_ctx=git_ctx,
                target_commit=target_commit,
                canonical_path=canonical_path,
            )

            if dest_path.exists():
                try:
                    current_bytes = dest_path.read_bytes()
                except OSError:
                    current_bytes = b""
                if current_bytes != target_bytes:
                    updated += 1
            else:
                written += 1

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(target_bytes)

        deleted = 0
        if delete_missing:
            current_scoped = self._collect_current_scoped_files(module_name=module_name, config=config)
            for current_path in sorted(current_scoped):
                candidate = (workspace_root_path / Path(current_path)).resolve()
                if str(candidate) not in mapped_target_paths and candidate.exists() and candidate.is_file():
                    candidate.unlink()
                    deleted += 1

        return {
            "module_name": module_name,
            "resolved_target": target_ref,
            "target_commit": target_commit,
            "written_count": written,
            "updated_count": updated,
            "deleted_count": deleted,
            "workspace_root": str(workspace_root_path),
        }

    def show_checkpoint(self, module_name: str, target: str = "latest") -> dict:
        module_name = self._normalize_module_name(module_name)
        git_ctx = self._history_context_for_read(module_name)
        has_repo = (Path(git_ctx["cwd"]) / ".git").exists() or (
            git_ctx.get("git_dir") is not None and Path(git_ctx.get("git_dir")).exists()
        )
        if not has_repo:
            raise FileNotFoundError(f"No checkpoint history found for '{module_name}'.")

        target_ref = self._resolve_checkpoint_target(git_ctx=git_ctx, target=target)
        commit_resolve = self._run_git(
            ["rev-parse", target_ref],
            cwd=git_ctx["cwd"],
            check=False,
            git_dir=git_ctx.get("git_dir"),
            work_tree=git_ctx.get("work_tree"),
        )
        if commit_resolve.returncode != 0:
            raise ValueError(f"Could not resolve checkpoint target '{target}' for '{module_name}'.")
        commit = (commit_resolve.stdout or "").strip()

        pretty = self._run_git(
            ["show", "-s", "--pretty=format:%H|%cI|%s", commit],
            cwd=git_ctx["cwd"],
            git_dir=git_ctx.get("git_dir"),
            work_tree=git_ctx.get("work_tree"),
        )
        commit_id, committed_at, message = (pretty.stdout or "").strip().split("|", 2)

        tags_raw = self._run_git(
            ["tag", "--points-at", commit],
            cwd=git_ctx["cwd"],
            git_dir=git_ctx.get("git_dir"),
            work_tree=git_ctx.get("work_tree"),
        )
        tags = sorted([line.strip() for line in (tags_raw.stdout or "").splitlines() if line.strip()])

        status_raw = self._run_git(
            ["show", "--name-status", "--pretty=format:", commit],
            cwd=git_ctx["cwd"],
            git_dir=git_ctx.get("git_dir"),
            work_tree=git_ctx.get("work_tree"),
        )
        changed_files = []
        added = 0
        modified = 0
        deleted = 0
        for line in (status_raw.stdout or "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split("\t", 1)
            if len(parts) != 2:
                continue
            status, path = parts
            changed_files.append({"status": status, "path": path})
            if status.startswith("A"):
                added += 1
            elif status.startswith("D"):
                deleted += 1
            else:
                modified += 1

        return {
            "module_name": module_name,
            "target": target,
            "commit": commit_id,
            "committed_at": committed_at,
            "message": message,
            "tags": tags,
            "changed_files_count": len(changed_files),
            "added_count": added,
            "modified_count": modified,
            "deleted_count": deleted,
            "changed_files": changed_files,
        }

    def _extract_version_from_message(self, message: str):
        match = re.search(r"\bversion=(\d+\.\d+\.\d+)\b", str(message))
        if not match:
            return None
        return match.group(1)

    def _list_local_checkpoints_with_tags(self, module_name: str) -> list:
        module_name = self._normalize_module_name(module_name)
        git_dir = self._module_history_git_dir(module_name)
        if not (git_dir / ".git").exists():
            return []

        tags_raw = self._run_git(["show-ref", "--tags"], cwd=git_dir, check=False)
        commit_tags = {}
        if tags_raw.returncode == 0:
            for line in (tags_raw.stdout or "").splitlines():
                if not line.strip():
                    continue
                commit, ref = line.split(" ", 1)
                tag = ref.rsplit("/", 1)[-1]
                commit_tags.setdefault(commit, []).append(tag)

        log = self._run_git(
            ["log", "--reverse", "--pretty=format:%H|%cI|%s"],
            cwd=git_dir,
            check=False,
        )
        if log.returncode != 0:
            return []

        checkpoints = []
        for line in (log.stdout or "").splitlines():
            if not line.strip():
                continue
            commit, committed_at, message = line.split("|", 2)
            checkpoints.append(
                {
                    "commit": commit,
                    "committed_at": committed_at,
                    "message": message,
                    "version": self._extract_version_from_message(message),
                    "tags": sorted(commit_tags.get(commit, [])),
                }
            )
        return checkpoints

    def _rebuild_history_repo(self, source_git_dir: Path, kept_entries: list, output_git_dir: Path):
        output_git_dir.mkdir(parents=True, exist_ok=True)
        self._run_git(["init"], cwd=output_git_dir)
        self._run_git(["config", "user.name", self.git_user_name], cwd=output_git_dir)
        self._run_git(["config", "user.email", self.git_user_email], cwd=output_git_dir)

        commit_map = {}

        for entry in kept_entries:
            for existing in output_git_dir.iterdir():
                if existing.name == ".git":
                    continue
                if existing.is_dir():
                    shutil.rmtree(existing)
                else:
                    existing.unlink()

            with subprocess.Popen(
                ["git", "archive", entry["commit"]],
                cwd=str(source_git_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as archive_process:
                extract_result = subprocess.run(
                    ["tar", "-x", "-C", str(output_git_dir)],
                    stdin=archive_process.stdout,
                    capture_output=True,
                    check=False,
                )
                if archive_process.stdout is not None:
                    archive_process.stdout.close()
                archive_stderr = b""
                if archive_process.stderr is not None:
                    archive_stderr = archive_process.stderr.read()
                archive_return = archive_process.wait()
            archive_stderr = archive_stderr.decode("utf-8", errors="ignore")

            if archive_return != 0:
                raise RuntimeError(
                    f"Failed to archive commit {entry['commit']}: {archive_stderr}"
                )
            if extract_result.returncode != 0:
                extract_stderr = (extract_result.stderr or b"").decode("utf-8", errors="ignore")
                raise RuntimeError(
                    f"Failed to extract commit {entry['commit']} archive: {extract_stderr}"
                )

            self._run_git(["add", "-A"], cwd=output_git_dir)
            env = deepcopy(os.environ)
            if entry.get("committed_at"):
                env["GIT_AUTHOR_DATE"] = entry["committed_at"]
                env["GIT_COMMITTER_DATE"] = entry["committed_at"]
            commit_result = subprocess.run(
                ["git", "commit", "--allow-empty", "-m", entry["message"]],
                cwd=str(output_git_dir),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            if commit_result.returncode != 0:
                raise RuntimeError(
                    "Failed to commit rebuilt checkpoint:\n"
                    f"STDOUT: {(commit_result.stdout or '').strip()}\n"
                    f"STDERR: {(commit_result.stderr or '').strip()}"
                )

            new_commit = (self._run_git(["rev-parse", "HEAD"], cwd=output_git_dir).stdout or "").strip()
            commit_map[entry["commit"]] = new_commit
            for tag in entry.get("tags", []):
                self._run_git(["tag", "-f", tag, new_commit], cwd=output_git_dir)

        return commit_map

    def prune_checkpoints(
        self,
        module_name: str,
        prune_commit: str = None,
        prune_version: str = None,
        dry_run: bool = False,
    ) -> dict:
        module_name = self._normalize_module_name(module_name)
        if prune_commit and prune_version:
            raise ValueError("Use either prune_commit or prune_version, not both.")

        git_dir = self._module_history_git_dir(module_name)
        if not (git_dir / ".git").exists():
            raise FileNotFoundError(f"No local checkpoint history found for '{module_name}'.")

        entries = self._list_local_checkpoints_with_tags(module_name=module_name)
        if not entries:
            return {
                "module_name": module_name,
                "removed_count": 0,
                "kept_count": 0,
                "removed_commits": [],
                "kept_commits": [],
            }

        removed = []
        kept = []
        for entry in entries:
            remove_entry = False
            if prune_commit:
                remove_entry = entry["commit"].startswith(prune_commit)
            elif prune_version:
                remove_entry = entry.get("version") == prune_version
            else:
                remove_entry = entry.get("version") == "0.0.0"

            if remove_entry:
                removed.append(entry)
            else:
                kept.append(entry)

        if dry_run:
            return {
                "module_name": module_name,
                "removed_count": len(removed),
                "kept_count": len(kept),
                "removed_commits": [item["commit"] for item in removed],
                "kept_commits": [item["commit"] for item in kept],
                "history_repo": str(git_dir),
                "dry_run": True,
            }

        temp_root = Path(tempfile.mkdtemp(prefix=f"paa_prune_{module_name}_"))
        rebuilt_git_dir = temp_root / "git"
        try:
            self._rebuild_history_repo(
                source_git_dir=git_dir,
                kept_entries=kept,
                output_git_dir=rebuilt_git_dir,
            )

            if git_dir.exists():
                shutil.rmtree(git_dir)
            shutil.copytree(rebuilt_git_dir, git_dir)
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)

        return {
            "module_name": module_name,
            "removed_count": len(removed),
            "kept_count": len(kept),
            "removed_commits": [item["commit"] for item in removed],
            "kept_commits": [item["commit"] for item in kept],
            "history_repo": str(git_dir),
            "dry_run": False,
        }

    def export_pruned_history(
        self,
        module_name: str,
        prune_commit: str = None,
        prune_version: str = "0.0.0",
    ) -> dict:
        module_name = self._normalize_module_name(module_name)
        if prune_commit and prune_version:
            raise ValueError("Use either prune_commit or prune_version, not both.")

        source_git_dir = self._module_history_git_dir(module_name)
        if not (source_git_dir / ".git").exists():
            return None

        entries = self._list_local_checkpoints_with_tags(module_name=module_name)
        kept = []
        for entry in entries:
            remove_entry = False
            if prune_commit:
                remove_entry = entry["commit"].startswith(prune_commit)
            elif prune_version is not None:
                remove_entry = entry.get("version") == prune_version
            if not remove_entry:
                kept.append(entry)

        temp_root = Path(tempfile.mkdtemp(prefix=f"paa_history_export_{module_name}_"))
        export_worktree_dir = temp_root / "git"
        self._rebuild_history_repo(
            source_git_dir=source_git_dir,
            kept_entries=kept,
            output_git_dir=export_worktree_dir,
        )

        export_git_repo_dir = temp_root / "git_repo"
        shutil.copytree(export_worktree_dir / ".git", export_git_repo_dir)

        return {
            "module_name": module_name,
            "temp_root": str(temp_root),
            "worktree_dir": str(export_worktree_dir),
            "git_repo_dir": str(export_git_repo_dir),
            "removed_count": len(entries) - len(kept),
            "kept_count": len(kept),
        }
