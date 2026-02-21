from python_modules.components.paa_deps.mkdocs_handler import MkDocsHandler


def test_mkdocs_handler_empty_markdown_detection(tmp_path):
    project_dir = tmp_path / "project"
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(parents=True)

    empty_md = docs_dir / "empty.md"
    empty_md.write_text("\n \t", encoding="utf-8")

    non_empty_md = docs_dir / "non_empty.md"
    non_empty_md.write_text("content", encoding="utf-8")

    handler = MkDocsHandler(package_name="m", docs_file_paths={}, project_name=str(project_dir))
    assert handler._is_markdown_empty(str(empty_md)) is True
    assert handler._is_markdown_empty(str(non_empty_md)) is False


def test_mkdocs_handler_writes_repo_link_when_configured(tmp_path):
    project_dir = tmp_path / "project"
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "index.md").write_text("intro", encoding="utf-8")

    handler = MkDocsHandler(
        package_name="m",
        docs_file_paths={},
        project_name=str(project_dir),
        source_repo_url="https://github.com/example/repo",
        source_repo_name="PPR Repo",
    )
    handler.create_mkdocs_yml()

    mkdocs_yml = (project_dir / "mkdocs.yml").read_text(encoding="utf-8")
    assert "repo_url: https://github.com/example/repo" in mkdocs_yml
    assert "repo_name: PPR Repo" in mkdocs_yml


def test_mkdocs_handler_always_writes_nav_intro(tmp_path):
    project_dir = tmp_path / "project"
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "index.md").write_text("intro", encoding="utf-8")

    handler = MkDocsHandler(package_name="m", docs_file_paths={}, project_name=str(project_dir))
    handler.create_mkdocs_yml()

    mkdocs_yml = (project_dir / "mkdocs.yml").read_text(encoding="utf-8")
    assert "nav:" in mkdocs_yml
    assert "- Intro: index.md" in mkdocs_yml
