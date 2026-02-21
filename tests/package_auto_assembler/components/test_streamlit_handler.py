from python_modules.components.paa_deps.streamlit_handler import StreamlitHandler


def test_streamlit_handler_run_app_builds_command(tmp_path, monkeypatch):
    streamlit_file = tmp_path / "app.py"
    streamlit_file.write_text("print('hello')\n", encoding="utf-8")

    calls = {}

    def _fake_run(cmd, check):
        calls["cmd"] = cmd
        calls["check"] = check
        return 0

    monkeypatch.setattr(
        "python_modules.components.paa_deps.streamlit_handler.subprocess.run",
        _fake_run,
    )

    handler = StreamlitHandler()
    handler.run_app(streamlit_filepath=str(streamlit_file), host="127.0.0.1", port="9876")

    assert calls["check"] is True
    assert calls["cmd"][0:3] == ["streamlit", "run", str(streamlit_file)]
    assert "--server.address=127.0.0.1" in calls["cmd"]
    assert "--server.port=9876" in calls["cmd"]


def test_streamlit_handler_prep_custom_config_creates_backup(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    streamlit_dir = fake_home / ".streamlit"
    streamlit_dir.mkdir(parents=True)

    current_config = streamlit_dir / "config.toml"
    current_config.write_text("old = true\n", encoding="utf-8")

    new_config = tmp_path / "new.toml"
    new_config.write_text("new = true\n", encoding="utf-8")

    monkeypatch.setattr(
        "python_modules.components.paa_deps.streamlit_handler.os.path.expanduser",
        lambda _: str(streamlit_dir),
    )

    handler = StreamlitHandler()
    handler._prep_custom_config(str(new_config))

    backup = streamlit_dir / "config_backup.toml"
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == "old = true\n"
    assert current_config.read_text(encoding="utf-8") == "new = true\n"
