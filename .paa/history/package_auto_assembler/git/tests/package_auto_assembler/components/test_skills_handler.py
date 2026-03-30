from python_modules.components.paa_deps.skills_handler import SkillsHandler
import python_modules.components.paa_deps.skills_handler as skills_handler_module


def test_skills_handler_resolve_codex_target_uses_agents_path(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)
    (repo / "AGENTS.md").write_text("# agents\n", encoding="utf-8")

    monkeypatch.chdir(nested)

    sh = SkillsHandler()
    destination = sh.resolve_destination_root(target="codex")

    assert destination == (repo / ".agents" / "skills").resolve()


def test_skills_handler_auto_detect_single_target_from_ancestry(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    nested = repo / "x" / "y"
    nested.mkdir(parents=True)
    (repo / ".agents").mkdir()

    monkeypatch.chdir(nested)

    sh = SkillsHandler()
    destination = sh.resolve_destination_root()

    assert destination == (repo / ".agents" / "skills").resolve()


def test_skills_handler_auto_detect_ambiguous_targets_raises(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    nested = repo / "z"
    nested.mkdir(parents=True)
    (repo / ".agents").mkdir()
    (repo / ".claude").mkdir()

    monkeypatch.chdir(nested)

    sh = SkillsHandler()

    try:
        sh.resolve_destination_root()
    except ValueError as exc:
        assert "Both codex and claude targets were detected." in str(exc)
    else:
        assert False, "Expected ValueError for ambiguous auto-detection."


def test_skills_handler_target_name_for_agents_path():
    sh = SkillsHandler()
    assert sh._target_name_for_path(sh.resolve_destination_root(output_dir="/tmp/.agents/skills")) == "codex"


def test_skills_handler_resolve_package_skills_dir_from_tracking(tmp_path, monkeypatch):
    package_name = "package_auto_assembler"
    package_root = tmp_path / package_name
    tracked_skills = package_root / ".paa.tracking" / "skills"
    tracked_skills.mkdir(parents=True)
    (tracked_skills / "s1").mkdir()
    (tracked_skills / "s1" / "SKILL.md").write_text("# skill\n", encoding="utf-8")

    monkeypatch.setattr(skills_handler_module.pkg_resources, "files", lambda _name: package_root)

    sh = SkillsHandler()
    module_name, skills_root = sh.resolve_package_skills_dir("package-auto-assembler")

    assert module_name == "package_auto_assembler"
    assert skills_root == tracked_skills


def test_skills_handler_codex_target_falls_back_to_project_root_without_markers(tmp_path, monkeypatch):
    nested = tmp_path / "no_markers" / "deep"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    sh = SkillsHandler()
    destination = sh.resolve_destination_root(target="codex")

    assert destination == (fake_home / ".agents" / "skills").resolve()


def test_skills_handler_auto_detect_falls_back_to_codex_when_no_markers(tmp_path, monkeypatch):
    nested = tmp_path / "no_markers" / "deeper"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    sh = SkillsHandler()
    destination = sh.resolve_destination_root()

    assert destination == (fake_home / ".agents" / "skills").resolve()
