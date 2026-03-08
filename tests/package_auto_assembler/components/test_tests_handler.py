from python_modules.components.paa_deps.tests_handler import TestsHandler


def test_tests_handler_prepare_tests(tmp_path):
    tests_src = tmp_path / "tests_src"
    tests_src.mkdir()
    (tests_src / "test_x.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")

    setup_dir = tmp_path / "setup"
    setup_dir.mkdir()

    handler = TestsHandler(tests_dir=str(tests_src), setup_directory=str(setup_dir))
    assert handler.prepare_tests() is True
    assert (setup_dir / "tests" / "test_x.py").exists()
