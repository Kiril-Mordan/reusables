from python_modules.components.paa_deps.artifacts_handler import ArtifactsHandler


def test_artifacts_handler_load_additional_artifacts(tmp_path):
    artifacts_dir = tmp_path / "artifacts_src"
    artifacts_dir.mkdir()
    (artifacts_dir / "a.txt").write_text("a", encoding="utf-8")
    (artifacts_dir / "b.txt").write_text("b", encoding="utf-8")

    handler = ArtifactsHandler()
    found = handler.load_additional_artifacts(str(artifacts_dir))

    assert set(found.keys()) == {"a.txt", "b.txt"}
    assert all(str(artifacts_dir) in path for path in found.values())


def test_artifacts_handler_make_manifest_copies_files(tmp_path, monkeypatch):
    setup_dir = tmp_path / "setup"
    setup_dir.mkdir()
    src_file = tmp_path / "artifact.txt"
    src_file.write_text("artifact-content", encoding="utf-8")

    handler = ArtifactsHandler(
        setup_directory=str(setup_dir),
        module_name="sample_pkg",
        artifacts_filepaths={"artifacts/artifact.txt": str(src_file)},
    )

    monkeypatch.setattr(
        "python_modules.components.paa_deps.artifacts_handler.importlib.metadata.version",
        lambda _pkg: "9.9.9",
    )

    handler.make_manifest()

    copied_file = setup_dir / "artifacts" / "artifact.txt"
    assert copied_file.exists()
    assert copied_file.read_text(encoding="utf-8") == "artifact-content"
    assert ".paa.tracking/.paa.version" in handler.artifacts_filepaths
    assert any(
        line.strip() == "include sample_pkg/artifacts/artifact.txt"
        for line in handler.manifest_lines
    )
