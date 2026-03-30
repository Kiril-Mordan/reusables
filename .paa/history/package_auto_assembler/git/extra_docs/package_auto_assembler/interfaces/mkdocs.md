# MkDocs Interface

## About

PAA can build package-scoped static documentation sites with MkDocs.
Core dependencies used under the hood:
- [MkDocs](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)

Each package can have its own docs site.
For overall documentation strategy (README + MkDocs + release notes with minimal duplication), see `concepts/documentation_flow.md`.

## What PAA Uses As Inputs

Typical package docs inputs include:

- main module docstring (`python_modules/<package>.py`) for intro/index
- optional PyPI/license badges shown on intro page
- package description markdown (often converted from notebook)
- release notes markdown
- extra docs files from `extra_docs/<package>/`:
  - `.md` copied to docs pages
  - `.ipynb` converted to markdown
  - nested folders preserved
- image files (including drawio-generated PNGs and notebook outputs)

From existing PAA notebook/docs flow:
- module docstring is used as package intro
- description and release notes are separate tabs/pages
- diagrams can be displayed as separate tabs/pages
- images referenced by markdown are not turned into separate tabs/pages

## Build Flow

In normal CLI usage:

```bash
paa test-install your-package-1 --build-mkdocs
```

This runs package docs preparation and mkdocs build as part of test-install.

Under the hood, the flow is equivalent to:
1. collect docs inputs
2. create mkdocs project dir
3. move markdown/images into docs tree
4. generate index and nav (`mkdocs.yml`)
5. build static site

## Viewing Docs

### Extract static site from installed package

```bash
paa extract-module-site your-package-1 --output-dir ./site_out
```

Open `./site_out/index.html` in browser.

### Serve docs through API routes

When using PAA FastAPI routing, packaged docs can be mounted and served from package docs path, e.g.:

`/<package-name>/docs`

Example:

```bash
paa run-api-routes --package-labels your-package-1 --host 127.0.0.1 --port 8000
```

With default scaffolded routes in `api_routes/your_package_1.py`:
- Open package docs site: `http://127.0.0.1:8000/your-package-1/docs/`

## Operational Commands

Build package docs during test-install:

```bash
paa test-install your-package-1 --build-mkdocs
```

Extract packaged docs site from installed package:

```bash
paa extract-module-site your-package-1 --output-dir ./site_out
```

Refresh drawio-derived diagrams used by docs:

```bash
paa convert-drawio-to-png --label-name your-package-1
```

Serve packaged docs through API routes:

```bash
paa run-api-routes --package-labels your-package-1 --host 127.0.0.1 --port 8000
```

## Deployment

Built MkDocs output is static HTML, so it can be published to static hosting:

- GitHub Pages
- Azure static hosting/web apps
- object storage + CDN static site setups

PAA CI/CD templates can be adapted to deploy these built docs artifacts automatically.

## Drawio And Images

Drawio conversion can be used to keep docs diagrams current:

```bash
paa convert-drawio-to-png --label-name your-package-1
```

Before conversion, PAA cleans stale drawio-generated PNGs for the selected package while preserving notebook-generated PNGs.
Drawio-derived files and docs copied from `extra_docs/<package>/` are both materialized in `.paa/docs` with `<package>-*` prefixed names; avoid duplicate base names to prevent collisions.

## Troubleshooting

- Empty markdown files are excluded from mkdocs nav.
- Missing image warnings usually mean stale image links or missing generated files.
- Notebook conversion errors indicate invalid notebook JSON/schema and should be fixed in source notebook.
- If old package docs tabs persist, rebuild package docs to refresh package-scoped docs output.
