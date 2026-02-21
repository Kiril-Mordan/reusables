from python_modules.components.paa_deps.drawio_handler import DrawioHandler


def test_drawio_handler_prepare_drawio(tmp_path):
    drawio_file = tmp_path / "m.drawio"
    drawio_file.write_text("<mxfile/>", encoding="utf-8")

    setup_dir = tmp_path / "setup"
    setup_dir.mkdir()

    handler = DrawioHandler(drawio_filepath=str(drawio_file), setup_directory=str(setup_dir))
    assert handler.prepare_drawio() is True
    assert (setup_dir / ".paa.tracking" / ".drawio").exists()
