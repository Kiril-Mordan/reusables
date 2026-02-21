from python_modules.components.paa_deps.version_handler import VersionHandler


def test_version_handler_add_update_and_increment(tmp_path):
    versions_file = tmp_path / "versions.yml"
    log_file = tmp_path / "versions.csv"

    handler = VersionHandler(
        versions_filepath=str(versions_file),
        log_filepath=str(log_file),
        read_files=True,
    )

    handler.add_package("pkg_a")
    assert handler.get_version("pkg_a") == "0.0.1"

    handler.update_version("pkg_a", "1.2.3")
    assert handler.get_version("pkg_a") == "1.2.3"

    handler.increment_version("pkg_a", increment_type="patch", usepip=False)
    assert handler.get_version("pkg_a") == "1.2.4"

    logs = handler.get_logs()
    assert {"Timestamp", "Package", "Version"}.issubset(set(logs.columns))
    assert "pkg_a" in set(logs["Package"].tolist())

    handler._close_log_file()
