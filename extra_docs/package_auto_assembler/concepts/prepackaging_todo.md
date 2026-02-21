# Prepackaging TODO

Use this checklist before running `paa test-install` or `paa make-package`.

## Core Module Checklist

- [ ] Package main module exists in `module_dir` with exact package file name:
  - `python_modules/<package_name>.py`
- [ ] Main module is the assembly point for packaged logic.
- [ ] Local components are wired through main module before interface use.
- [ ] Component code is import-safe and package-ready (no local machine-only paths).
- [ ] Module-level docstring is present and reflects current package purpose.

## Component Wiring Rules

- [ ] Component modules in `python_modules/components/` do not import each other directly.
- [ ] Cross-component dependencies are passed via main module wiring (single-module-package pattern).
- [ ] Interface modules (`cli`, `api_routes`, `streamlit`, `mcp`) import from packaged module namespace, not component file paths.
- [ ] When using handler-style composition, prefer `attrsx` conventions for consistency with PAA patterns.
- [ ] Keep selected package components free of component-to-component imports; packaging merge now validates this and fails early on violations.

## Metadata And Config

- [ ] `__package_metadata__` is present (at least minimal fields as needed).
- [ ] Metadata fields are valid and current (`author`, `author_email`, `description`, URLs, classifiers, extras, etc.).
- [ ] If used, `artifact_urls` entries are correct and reachable.
- [ ] `.paa.config` paths and package settings reflect current repo layout.
- [ ] Config-derived fields are intentional (`license_label`, `docs_url`, `source_repo_url`, `source_repo_name`, `classifiers`).

## Interface Files

### CLI (`cli/<package_name>.py`)
- [ ] One file per package with matching package name.
- [ ] `click` command group and command registration are valid.
- [ ] Optional `__cli_metadata__` command name is intentional.

### FastAPI (`api_routes/<package_name>.py`)
- [ ] One file per package with matching package name.
- [ ] Exposes `router = APIRouter(...)`.
- [ ] Route prefix and endpoint naming are intentional.

### Streamlit (`streamlit/<package_name>.py`)
- [ ] One file per package with matching package name.
- [ ] Imports come from packaged module namespace.
- [ ] App code is safe to run in configured environment.

### MCP (`mcp/<package_name>.py`)
- [ ] One file per package with matching package name.
- [ ] Exposes `mcp = FastMCP(...)` and `@mcp.tool()` functions.
- [ ] Tool names and docstrings are stable and clear for agent usage.

### MkDocs Inputs
- [ ] `example_notebooks/<package_name>.ipynb` is valid if README generation depends on it.
- [ ] `extra_docs/<package_name>/` content is organized and non-empty.
- [ ] Image references are valid; avoid drawio/extra-doc naming collisions after prefixing.

## Artifacts, Tests, And Licenses

- [ ] Optional artifacts are prepared under `artifacts/<package_name>/`.
- [ ] Optional tests exist under `tests/<package_name>/` when needed.
- [ ] Package-specific license/notice files are present if required by your setup.
- [ ] Large or generated files are included intentionally.

## Quality Gates

- [ ] Run lints before packaging (recommended):
  - `paa run-pylint-tests --module-name <package_name>`
- [ ] Address obvious pylint findings or document accepted exceptions.
- [ ] Keep code style/structure consistent so maintenance remains manageable.

## Final Packaging Checks

- [ ] Run local package validation:
  - `paa test-install <package_name> --skip-deps-install`
- [ ] If docs are part of release:
  - `paa test-install <package_name> --build-mkdocs --skip-deps-install`
- [ ] For release-ready build:
  - `paa make-package <package_name>`
