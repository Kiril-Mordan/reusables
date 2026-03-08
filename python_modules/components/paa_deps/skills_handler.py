import logging
import shutil
from pathlib import Path
import importlib.resources as pkg_resources
import yaml
import attrs
import attrsx


@attrsx.define
class SkillsHandler:

    """
    Handles extraction and cleanup of package skills for agent targets.
    """

    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Skills Handler')
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

    def _initialize_logger(self):
        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)
            self.logger = logger

    def _find_target_root_by_marker(self,
                                    target: str) -> Path:
        marker_dir = ".agents" if target == "codex" else ".claude"
        marker_md = "AGENTS.md" if target == "codex" else "CLAUDE.md"

        current = Path.cwd().resolve()
        for candidate in [current, *current.parents]:
            if (candidate / marker_dir).exists() or (candidate / marker_md).exists():
                return candidate
        return None

    def _codex_user_skills_root(self) -> Path:
        return (Path.home() / ".agents" / "skills").resolve()

    def _detect_available_targets(self) -> list:
        targets = []
        if self._find_target_root_by_marker("codex") is not None:
            targets.append("codex")
        if self._find_target_root_by_marker("claude") is not None:
            targets.append("claude")
        return targets

    def resolve_destination_root(self,
                                 output_dir: str = None,
                                 target: str = None) -> Path:
        if output_dir:
            return Path(output_dir).resolve()

        if target:
            target = target.lower()
            if target == "codex":
                target_root = self._find_target_root_by_marker("codex")
                if target_root is None:
                    return self._codex_user_skills_root()
                return (target_root / ".agents" / "skills").resolve()
            if target == "claude":
                target_root = self._find_target_root_by_marker("claude")
                if target_root is None:
                    raise ValueError(
                        "Could not auto-detect claude target root. "
                        "Provide --output-dir or run in a repository with .claude or CLAUDE.md."
                    )
                return (target_root / ".claude" / "skills").resolve()
            raise ValueError(f"Unsupported target: {target}")

        available_targets = self._detect_available_targets()
        if len(available_targets) == 1:
            detected_target = available_targets[0]
            if detected_target == "codex":
                target_root = self._find_target_root_by_marker("codex")
                return (target_root / ".agents" / "skills").resolve()
            target_root = self._find_target_root_by_marker("claude")
            return (target_root / ".claude" / "skills").resolve()

        if len(available_targets) > 1:
            raise ValueError(
                "Both codex and claude targets were detected. "
                "Provide --target codex|claude or --output-dir."
            )

        return self._codex_user_skills_root()

    def resolve_package_skills_dir(self,
                                   package_name: str) -> tuple:
        module_name = package_name.replace("-", "_")
        package_root = Path(pkg_resources.files(module_name))

        candidates = [
            package_root / ".paa.tracking" / "skills" / module_name,
            package_root / ".paa.tracking" / "skills",
            package_root / "skills" / module_name,
            package_root / "skills",
        ]

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return module_name, candidate

        raise FileNotFoundError(
            f"No skills directory found in installed package {package_name}."
        )

    def _skill_dirs_from_root(self,
                              skills_root: Path) -> list:
        if not skills_root.exists():
            return []
        return sorted(
            [path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").exists()],
            key=lambda p: p.name.lower()
        )

    def _target_name_for_path(self,
                              destination_root: Path) -> str:
        parts = {part.lower() for part in destination_root.parts}
        if ".agents" in parts:
            return "codex"
        if ".claude" in parts:
            return "claude"
        return "custom"

    def _write_skill_marker(self,
                            skill_dir: Path,
                            package_name: str,
                            skill_name: str,
                            target: str):
        marker = {
            "managed_by": "paa",
            "source_package": package_name,
            "skill_name": skill_name,
            "installed_target": target,
        }
        marker_path = skill_dir / ".paa_skill_meta.yml"
        with open(marker_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(marker, file, sort_keys=False)

    def extract_skill(self,
                      package_name: str,
                      skill_name: str,
                      output_dir: str = None,
                      target: str = None) -> Path:
        module_name, skills_root = self.resolve_package_skills_dir(package_name)
        source_skill_dir = skills_root / skill_name
        if not source_skill_dir.exists() or not source_skill_dir.is_dir():
            raise FileNotFoundError(
                f"Skill '{skill_name}' was not found for package '{package_name}'."
            )
        if not (source_skill_dir / "SKILL.md").exists():
            raise FileNotFoundError(
                f"Skill '{skill_name}' does not contain SKILL.md."
            )

        destination_root = self.resolve_destination_root(output_dir=output_dir, target=target)
        destination_skill_dir = destination_root / module_name / skill_name
        destination_skill_dir.parent.mkdir(parents=True, exist_ok=True)
        if destination_skill_dir.exists():
            shutil.rmtree(destination_skill_dir)
        shutil.copytree(source_skill_dir, destination_skill_dir)

        resolved_target = target.lower() if target else self._target_name_for_path(destination_root)
        self._write_skill_marker(destination_skill_dir, module_name, skill_name, resolved_target)

        return destination_skill_dir

    def extract_skills(self,
                       package_name: str,
                       output_dir: str = None,
                       target: str = None) -> tuple:
        module_name, skills_root = self.resolve_package_skills_dir(package_name)
        source_skills = self._skill_dirs_from_root(skills_root)
        if not source_skills:
            raise FileNotFoundError(
                f"No skills with SKILL.md were found for package '{package_name}'."
            )

        destination_root = self.resolve_destination_root(output_dir=output_dir, target=target)
        resolved_target = target.lower() if target else self._target_name_for_path(destination_root)

        installed = 0
        for source_skill_dir in source_skills:
            skill_name = source_skill_dir.name
            destination_skill_dir = destination_root / module_name / skill_name
            destination_skill_dir.parent.mkdir(parents=True, exist_ok=True)
            if destination_skill_dir.exists():
                shutil.rmtree(destination_skill_dir)
            shutil.copytree(source_skill_dir, destination_skill_dir)
            self._write_skill_marker(destination_skill_dir, module_name, skill_name, resolved_target)
            installed += 1

        return installed, destination_root / module_name

    def cleanup_agent_skills(self,
                             output_dir: str = None,
                             target: str = None) -> tuple:
        destination_root = self.resolve_destination_root(output_dir=output_dir, target=target)
        if not destination_root.exists():
            return 0, destination_root

        removed = 0
        marker_paths = list(destination_root.rglob(".paa_skill_meta.yml"))
        for marker_path in marker_paths:
            skill_dir = marker_path.parent
            try:
                with open(marker_path, "r", encoding="utf-8") as file:
                    marker_data = yaml.safe_load(file) or {}
                if marker_data.get("managed_by") != "paa":
                    continue
            except Exception:
                continue

            shutil.rmtree(skill_dir, ignore_errors=True)
            removed += 1

        return removed, destination_root
