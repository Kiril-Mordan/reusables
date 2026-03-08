from python_modules.components.paa_deps.ppr_handler import PprHandler


def test_ppr_handler_init_paa_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    handler = PprHandler()
    assert handler.init_paa_dir() is True
    assert (tmp_path / ".paa").exists()
