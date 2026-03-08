# Package Metadata

## About

`__package_metadata__` is a module-level dictionary used by PAA to enrich packaging outputs.
It is parsed from `python_modules/<package_name>.py` and used when generating setup/pyproject metadata and artifact behavior.

Minimal location pattern:

```python
__package_metadata__ = {
    "author": "Your Name",
    "author_email": "you@example.com",
}
```

## How PAA Uses It

At packaging time, PAA extracts `__package_metadata__` and maps it into:
- `setup.py` fields
- pyproject metadata generated under `.paa/pyproject/`
- artifact link handling (when `artifact_urls` is provided)

Some metadata is merged with PAA defaults (for example classifiers, docs URL, and license label fallback).

## Common Fields

Commonly used keys:
- `name`: package distribution name override (defaults to module name with `_` -> `-`)
- `description`
- `author`
- `author_email`
- `url` (homepage)
- `project_urls` (dict of additional links)
- `keywords` (list or comma-separated string)
- `classifiers` (list)
- `requires_python` (for pyproject generation)
- `readme` (defaults to `README.md`)
- `extras_require` (dict of optional dependency groups)
- `install_requires` (additional required dependencies)
- `artifact_urls` (dict of artifact name -> URL)

## Artifact URL Behavior

If `artifact_urls` is present, PAA converts each entry into an artifact link input during packaging.
Effectively, those URLs behave like files in `artifacts/<package_name>/` with `.link` semantics.

Example:

```python
__package_metadata__ = {
    "artifact_urls": {
        "usage_guide": "https://example.com/guide.pdf",
        "logo": "https://example.com/logo.png",
    }
}
```

## Merge Behavior Notes

- If `classifiers` are provided in metadata, they are merged with baseline classifiers.
- If metadata provides `url`, it is used as homepage/project URL source.
- `license_label` and docs URL can also come from PAA config/runtime values and are merged into final project metadata.
- PAA adds/keeps `aa-paa-tool` in `keywords` during metadata extraction.

## Fields Inherited From `.paa.config`

During `paa make-package` / `paa test-install`, selected packaging fields are injected from `.paa.config` into the assembler runtime and then merged with `__package_metadata__`.

Config-provided fields:
- `license_label`
- `docs_url`
- `source_repo_url`
- `source_repo_name`
- `classifiers` (baseline list)

Practical precedence behavior:
- metadata `url` remains homepage source when provided in `__package_metadata__`
- config `docs_url` is used as documentation URL when set
- metadata `classifiers` are merged with config/runtime classifiers (with development-status dedup logic)
- `source_repo_url` / `source_repo_name` feed docs-site source link generation (MkDocs integration)

## Minimal Example

```python
__package_metadata__ = {
    "author": "Your Name",
    "author_email": "you@example.com",
    "description": "Small utility package.",
    "keywords": ["python", "automation"],
}
```

## Extended Example

```python
__package_metadata__ = {
    "name": "your-package",
    "description": "Toolkit for internal automation.",
    "author": "Your Team",
    "author_email": "team@example.com",
    "url": "https://example.com/your-package",
    "project_urls": {
        "Source": "https://github.com/org/repo",
        "Issues": "https://github.com/org/repo/issues",
    },
    "keywords": ["python", "automation", "tooling"],
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
    ],
    "requires_python": ">=3.10",
    "extras_require": {
        "dev": ["pytest", "ruff"],
    },
    "artifact_urls": {
        "reference": "https://example.com/reference.pdf",
    },
}
```

## Related Docs

- Artifacts behavior: `components/artifacts.md`
- CLI interface metadata note: `interfaces/cli.md`
- PPR workflow context: `concepts/python_packaging_repo.md`
