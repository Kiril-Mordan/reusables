# `.paa.config` Reference

This file controls how the PAA repository behaves.

## Paths

- `module_dir`: Directory with package modules (`*.py`).
- `dependencies_dir`: Directory with shared local components.
- `example_notebooks_path`: Directory with example notebooks used for README generation.
- `licenses_dir`: Root directory for per-package license files (`<licenses_dir>/<package>/LICENSE`, `NOTICE`).
- `cli_dir`: Directory with package CLI modules.
- `api_routes_dir`: Directory with FastAPI route modules.
- `streamlit_dir`: Directory with Streamlit modules.
- `artifacts_dir`: Directory with packaged artifact folders.
- `drawio_dir`: Directory with drawio files.
- `extra_docs_dir`: Directory with package docs folders.
- `tests_dir`: Directory with package test folders.

Notes:
- These are optional in minimal `.paa.config` because runtime defaults are applied.
- In full `.paa.config`, all path keys are shown.

## Core Behavior

- `use_commit_messages`: If true, version/release behavior uses commit conventions.
- `check_vulnerabilities`: Enables vulnerability checks where applicable.
- `check_dependencies_licenses`: Enables dependency license checks where applicable.
- `add_artifacts`: Enables packaging/unfolding artifacts.
- `add_mkdocs_site`: Enables mkdocs site generation when requested by commands.
- `pylint_threshold`: Score threshold for pylint-oriented checks.

## Compatibility Settings

- `make_package_check_dependencies_compatibility`: Optional static compatibility check toggle for `make-package`.
- `test_install_check_dependencies_compatibility`: Optional static compatibility check toggle for `test-install`.
- `make_package_check_full_dependencies_compatibility`: Optional full resolver check toggle for `make-package`.
- `test_install_check_full_dependencies_compatibility`: Optional full resolver check toggle for `test-install`.

Notes:
- These are optional. If omitted or `null`, command defaults are used.

## License Related

- `license_path`: Optional explicit path to package license file.
- `notice_path`: Optional explicit path to package notice file.
- `license_label`: Optional docs/readme label.
- `license_badge`: Optional badge markdown.
- `allowed_licenses`: Optional allow-list for license checks.

## Docs and Repository Metadata

- `docs_url`: Optional docs URL used in metadata.
- `source_repo_url`: Optional source repository URL.
- `source_repo_name`: Optional source repository name.
- `classifiers`: Optional package classifiers list.

## Platform Integration

- `gh_pages_base_url`: Optional GitHub Pages base URL used in repository workflows/docs setup.
- `docker_username`: Optional Docker username used in repository workflow templates.

## Runtime/Build Related Optional Fields

- `default_version`: Optional version override when packaging.
- `python_version`: Optional target Python version for some commands.
- `kernel_name`: Optional notebook execution kernel name.
- `docs_file_paths`: Optional explicit docs mapping used by docs generation.
- `artifacts_filepaths`: Optional explicit artifacts mapping.

## Typical Modes

- Minimal init (`paa init-config`):
  - Focuses on core behavior and `pylint_threshold`.
  - Keeps advanced/path fields out of the default file for readability.
- Full init (`paa init-config --full`):
  - Shows all path fields.
  - Shows optional fields explicitly as `null`.
