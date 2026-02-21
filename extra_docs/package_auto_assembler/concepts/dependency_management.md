# Dependency Management in PAA

## Why PAA Uses Semi-Automatic Dependency Management

`package-auto-assembler` is designed to reduce manual packaging work while keeping control where needed.
For dependencies, this means:

- automatic extraction from Python source files;
- optional compatibility, vulnerability, and license checks;
- explicit override mechanisms when automatic behavior is not enough.

This is "semi-automatic" by design: defaults are optimized for low maintenance, but you can still force exact outcomes.

## How Extraction Works

During packaging-related commands, PAA builds requirements from imports in:

- main module (`module_dir/<package>.py`);
- local components from `dependencies_dir` referenced by the module;
- optional package modules (CLI, FastAPI routes, Streamlit) when present.

Import names are normalized to install names using mapping files (default mapping + `.paa/package_mapping.json` overrides).
For mapping-specific behavior and troubleshooting, see `components/import_mapping.md`.

## Control Markers in Source Code

PAA supports simple in-code control markers:

- `#@ <requirement>`: force-add a requirement line.
- `#! import ...`: mark as optional requirement (`extras_require` flow).
- `#-` on an import: exclude that import from automatic extraction.

### Example

```python
import pandas
import tensorflow #-
#@ tensorflow-gpu
#! import hnswlib #==0.8.0
```

Typical effect:

- `pandas` added automatically;
- `tensorflow` import ignored because of `#-`;
- `tensorflow-gpu` added explicitly by `#@`;
- optional dependency added from `#! ...`.

## Compatibility Checks

PAA supports two compatibility modes:

- Static compatibility check: validates declared constraints.
- Full resolver compatibility check: validates resolution behavior more deeply.

Defaults:

- `paa make-package`: static and full checks enabled by default.
- `paa test-install`: static enabled by default, full disabled by default.
- `paa check-deps-compat`: static check runs; add `--full` for full resolver check.

Config keys (optional) in `.paa.config`:

- `make_package_check_dependencies_compatibility`
- `test_install_check_dependencies_compatibility`
- `make_package_check_full_dependencies_compatibility`
- `test_install_check_full_dependencies_compatibility`

If omitted or set to `null`, command defaults are used.

## Security and License Checks

Dependency management in PAA also includes quality gates:

- Vulnerability checks via `pip-audit`.
- License checks against allowed labels (with normalization/mapping support).

Useful commands:

- `paa check-vulnerabilities <module>`
- `paa check-licenses <module>`

Supporting files:

- `.paa/package_licenses.json` for license label overrides.

## Main Config and Mapping Files

Files commonly used in dependency flows:

- `.paa.config`
- `.paa/package_mapping.json`
- `.paa/package_licenses.json`

Common config keys:

- `dependencies_dir`
- `check_vulnerabilities`
- `check_dependencies_licenses`
- compatibility keys listed above.

## Recommended Workflow

For normal package development:

1. `paa check-deps-compat <module>`
2. `paa test-install <module> --skip-deps-install` (and optionally `--build-mkdocs`)
3. `paa make-package <module>`

Use `--full` checks when preparing high-confidence releases or when constraints changed significantly.
