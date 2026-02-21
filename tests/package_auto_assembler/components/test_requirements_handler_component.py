import pytest

from python_modules.components.paa_deps.requirements_handler import RequirementsHandler


def test_requirements_handler_extract_requirements_parses_constraints(tmp_path):
    module_file = tmp_path / "mod.py"
    module_file.write_text(
        "\n".join(
            [
                "import requests #>=2.30.0",
                "import pandas as pd #[perf] >=2.1.0",
                "from sklearn.model_selection import train_test_split #>=1.3.0",
                "#! import uvicorn #>=0.29.0",
                "#@ customlib==1.0.0",
                "import os",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    handler = RequirementsHandler(
        module_filepath=str(module_file),
        package_mappings={"sklearn": "scikit-learn"},
        add_header=False,
    )
    reqs, optional = handler.extract_requirements()

    assert "requests>=2.30.0" in reqs
    assert "pandas[perf]>=2.1.0" in reqs
    assert "scikit-learn>=1.3.0" in reqs
    assert "customlib==1.0.0" in reqs
    assert "uvicorn>=0.29.0" in optional
    assert all("os" not in req for req in reqs)


def test_requirements_handler_compatibility_detects_conflict():
    handler = RequirementsHandler(add_header=False)

    with pytest.raises(ValueError):
        handler.check_requirements_compatibility(
            ["demo-pkg==1.0.0", "demo-pkg==2.0.0"]
        )


def test_requirements_handler_compatibility_accepts_compatible_constraints():
    handler = RequirementsHandler(add_header=False)

    conflicts = handler.check_requirements_compatibility(
        ["demo-pkg>=1.0.0", "demo-pkg<2.0.0", "other==3.1.0"],
        raise_error=False,
    )

    assert conflicts == []


def test_requirements_handler_full_compatibility_success(monkeypatch):
    class _Result:
        returncode = 0
        stdout = "Would install..."
        stderr = ""

    monkeypatch.setattr(
        "python_modules.components.paa_deps.requirements_handler.subprocess.run",
        lambda *args, **kwargs: _Result(),
    )

    handler = RequirementsHandler(add_header=False)
    out = handler.check_full_requirements_compatibility(["requests>=2.0.0"])

    assert out["ok"] is True


def test_requirements_handler_full_compatibility_conflict(monkeypatch):
    class _Result:
        returncode = 1
        stdout = ""
        stderr = "ResolutionImpossible"

    monkeypatch.setattr(
        "python_modules.components.paa_deps.requirements_handler.subprocess.run",
        lambda *args, **kwargs: _Result(),
    )

    handler = RequirementsHandler(add_header=False)

    with pytest.raises(ValueError):
        handler.check_full_requirements_compatibility(["demo==1.0", "demo==2.0"])
