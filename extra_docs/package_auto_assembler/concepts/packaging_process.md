# Packaging Process

## About

This page explains how PAA turns editable repository state into installable package artifacts.
It focuses on user-visible flow, key commands, and what happens in temporary packaging state.

For checkpoint semantics and history operations, see `concepts/checkpoint_history.md`.

## High-Level Flow

PAA packaging works as a staged transformation:

1. Start from unfolded PPR inputs (module, components, interfaces, docs, artifacts, tests, config).
2. Build temporary packaging state (setup directory + assembled files).
3. Build distribution artifacts (wheel/sdist).
4. Optionally install locally (`test-install`) or prepare release output (`make-package`).

The development layout and packaged layout are intentionally different.
This allows modular development while still producing consistent package outputs.

## Main Commands And What They Do

### `paa test-install <package>`

Primary local validation command.

What it does:
- reads `.paa.config` and resolves paths
- assembles temporary packaging state
- extracts/merges requirements from module and enabled interfaces
- optionally builds docs (`--build-mkdocs`)
- builds package artifacts and installs into current environment
- cleans temporary setup directory unless `--keep-temp-files` is used

### `paa make-package <package>`

Primary build command for release preparation.

What it does:
- runs the same core assembly/build steps as `test-install`
- applies release/version flow
- prepares distributable artifacts without local install step
- includes packaging tracking payload used by unfold/checkpoint workflows

### `paa unfold-package <package>`

State reconstruction command.

What it does:
- reads packaged tracking payload from installed package
- restores editable PPR-like structure in current repo
- rehydrates paths according to current `.paa.config`

## Temporary Packaging State

During packaging, PAA creates a temporary setup directory that acts as build staging area.
Typical staged content includes:

- assembled main module (with merged local dependencies when configured)
- generated `__init__.py`
- interface files (`cli.py`, `routes.py`, `streamlit.py`, `mcp_server.py`) when present
- `setup.py` and generated pyproject metadata snapshot
- README/docs/artifacts/tests payload intended for package distribution

Why this exists:
- isolate packaging from editable source layout
- ensure deterministic build inputs
- provide inspectable intermediate state for debugging

Debug tip:
- use `--keep-temp-files` with `test-install` to inspect staged files before cleanup.

## From Unfolded State To Packaged State

In unfolded repo state, package data is distributed across multiple directories (`python_modules`, `components`, `cli`, `api_routes`, `streamlit`, `mcp`, `extra_docs`, `artifacts`, `tests`, `.paa`).

Packaging converts this into package-internal structure:

- runtime package code
- optional interface entry modules
- optional docs site and artifacts
- tracking payload under `.paa.tracking` for reconstructing/editing later

This conversion is the core “assembly” step that bridges development ergonomics and distribution ergonomics.

## Structure Comparison: Unfolded vs Packaged

### Unfolded Structure (PPR workspace)

```text
.
├── .paa.config
├── .paa/
│   ├── tracking/
│   │   ├── lsts_package_versions.yml
│   │   └── version_logs.csv
│   ├── release_notes/
│   │   └── <package_name>.md
│   ├── requirements/
│   │   └── requirements_<package_name>.txt
│   ├── pyproject/
│   │   └── <package_name>.toml
│   └── docs/
│       └── <package_name>*.md
├── python_modules/
│   ├── <package_name>.py
│   └── components/
│       └── <package_name>/
│           ├── dep_1.py
│           └── subdir/
│               └── dep_2.py
├── cli/
│   └── <package_name>.py
├── api_routes/
│   └── <package_name>.py
├── streamlit/
│   └── <package_name>.py
├── mcp/
│   └── <package_name>.py
├── example_notebooks/
│   └── <package_name>.ipynb
├── extra_docs/
│   └── <package_name>/
│       ├── *.md / *.ipynb
│       └── subfolders...
├── artifacts/
│   └── <package_name>/
├── drawio/
│   └── <package_name>.drawio
├── skills/
│   └── <package_name>/
│       └── <skill_name>/SKILL.md
└── tests/
    └── <package_name>/
```

### Packaged Structure (installed package)

```text
<package_name>/
├── __init__.py
├── <package_name>.py
├── cli.py
├── routes.py
├── streamlit.py
├── mcp_server.py
├── README.md
├── LICENSE
├── NOTICE
├── artifacts/
│   └── ...
├── tests/
│   └── ...
└── .paa/
    └── tracking/
        ├── .paa.config
        ├── notebook.ipynb
        ├── pyproject.toml
        ├── release_notes.md
        ├── package_mapping.json
        ├── package_licenses.json
        ├── lsts_package_versions.yml
        ├── version_logs.csv
        ├── extra_docs/
        ├── skills/
        ├── git/
        └── git_repo/
```

## Merging Local Dependencies Into One Module

One of the core packaging transformations is merging local dependency components into the package module before build.

Why this exists:
- development can stay modular in unfolded repo state
- packaged output remains a single-module package shape expected by PAA assembly rules
- dependency extraction and packaging become more deterministic at build time

How it is used conceptually:
- source module comes from `module_dir/<package>.py`
- local components come from `dependencies_dir` when referenced by the package module
- packaging step composes these into one staged module in temporary setup state

Minimal example:

`python_modules/my_package.py` (before merge)

```python
"""
Simple package example.
"""

import requests
from .components.local_dependency_1 import normalize_name

def build_payload(name: str) -> dict:
    return {"name": normalize_name(name)}
```

`python_modules/components/local_dependency_1.py` (before merge)

```python
import requests
import re

def normalize_name(name: str) -> str:
    _ = requests.__name__
    cleaned = re.sub(r"\s+", " ", name.strip())
    return cleaned.lower()
```

`setup_dir/my_package.py` (after merge into one file)

```python
"""
Simple package example.
"""

import requests
import re

def normalize_name(name: str) -> str:
    _ = requests.__name__
    cleaned = re.sub(r"\s+", " ", name.strip())
    return cleaned.lower()

def build_payload(name: str) -> dict:
    return {"name": normalize_name(name)}
```

Merge assumptions shown above:
- component import lines are removed from the main module
- overlapping imports from main module and components are deduplicated
- module docstring from main module is preserved in assembled output

## Why Single-Module Packaging

PAA uses single-module packaged output to keep packaging behavior deterministic and operationally simple.

Practical benefits:
- one canonical packaged code boundary (assembled module)
- stable import surface for package interfaces
- deterministic dependency extraction from assembled module plus interface files
- fewer internal import-graph failure modes in packaged state
- clearer unfold/checkpoint reconstruction from packaged artifacts

Important constraints:
- component modules are intended as development-time building blocks
- cross-component wiring should be routed through the main module
- interface files should import from packaged module namespace, not component file paths
- selected components are validated during merge and packaging fails if they import other local components

Practical effect:
- unfolded structure stays readable and maintainable for development
- packaged structure remains consistent and portable for distribution/install

## Underlying Python Tooling

PAA orchestrates existing Python tooling rather than replacing build standards:

- `setuptools` for package build definitions (`setup.py`)
- `wheel`/sdist build process for distributable artifacts
- `pip` for local installation in `test-install`
- `mkdocs` (and material/plugins) for docs-site build when enabled
- dependency/security/license validation tooling integrated into packaging flow

PAA’s value is orchestration and automation around these tools in a multi-package repository workflow.

## Checkpoints And Packaged History (Brief)

Packaging can include checkpoint history payload used for later restore/checkout workflows.
`make-package` applies packaged-history sanitization rules (for example excluding local `0.0.0` history in packaged output).

For details, workflows, and prune/checkout semantics, see:
- `concepts/checkpoint_history.md`

## Related Docs

- PPR onboarding and repository setup: `concepts/python_packaging_repo.md`
- Preflight checks before build: `concepts/prepackaging_todo.md`
- Metadata mapping: `components/package_metadata.md`
- Artifacts behavior: `components/artifacts.md`
