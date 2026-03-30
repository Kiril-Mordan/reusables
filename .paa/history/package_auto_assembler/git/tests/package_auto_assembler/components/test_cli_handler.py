from python_modules.components.paa_deps.cli_handler import CliHandler


def test_cli_handler_prepare_script(tmp_path):
    source_cli = tmp_path / "source_cli.py"
    source_cli.write_text("def cli():\n    pass\n", encoding="utf-8")

    setup_dir = tmp_path / "setup"
    setup_dir.mkdir()

    handler = CliHandler(cli_module_filepath=str(source_cli), setup_directory=str(setup_dir))
    assert handler.prepare_script() is True
    assert (setup_dir / "cli.py").exists()
