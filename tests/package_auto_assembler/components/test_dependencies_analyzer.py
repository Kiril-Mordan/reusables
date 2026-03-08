from python_modules.components.paa_deps.dependencies_analyzer import DependenciesAnalyser


def test_extract_dependencies_names_parses_specifiers_and_extras():
    handler = DependenciesAnalyser()
    requirements = [
        "requests>=2.30.0",
        "pandas == 2.1.4",
        "xgboost<2.0; python_version >= '3.10'",
        "demo_pkg; extra == 'dev'",
    ]

    deps = handler._extract_dependencies_names(requirements)

    assert deps == ["requests", "pandas", "xgboost"]


def test_find_unexpected_licenses_without_raise():
    handler = DependenciesAnalyser(allowed_licenses=["mit", "apache-2.0"])
    licenses = {
        "root_pkg": "mit",
        "root_pkg.dep_a": "proprietary",
        "root_pkg.dep_b": "apache-2.0",
        "other_pkg": "gpl-3.0",
    }

    out = handler.find_unexpected_licenses_in_deps_tree(
        tree_dep_license=licenses,
        raise_error=False,
    )

    assert "root_pkg.dep_a" in out
    assert "other_pkg" in out
    assert out["root_pkg.dep_a"] == "proprietary"
    assert out["other_pkg"] == "gpl-3.0"
