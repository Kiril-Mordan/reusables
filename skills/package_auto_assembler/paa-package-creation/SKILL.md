---
name: paa-package-creation
description: Guide users through creating PAA packages with correct single-module wiring, component separation, attrsx-based composition patterns, and test-install validation.
---

# PAA Package Creation

Use this skill when users want to create, structure, validate, or review a package built with `package-auto-assembler`.

## Core Model: Single-Module Package

PAA is designed to produce **single-module packages**.

That means:

- The package entry module is `module_dir/<package_name>.py`.
- Main wiring happens in that file.
- Local components are merged/assembled through that module during packaging.

If this main module is missing or not wired correctly, package behavior will be unstable.

## Folder Structure Guidance

From `.paa.config`, typical paths are:

- `module_dir` (required): package main modules.
- `dependencies_dir`: local components.
- `cli_dir`: package CLI modules.
- `api_routes_dir`: FastAPI route modules.
- `streamlit_dir`: Streamlit modules.
- `example_notebooks_path`: notebook source for README.
- `extra_docs_dir`: package docs inputs.
- `artifacts_dir`: packaged files.
- `drawio_dir`: drawio diagrams for docs.
- `tests_dir`: package tests.

## Minimum Required Package Inputs

In `module_dir/<package_name>.py`, ensure:

1. Module docstring.
2. `__package_metadata__` dict.
3. Package logic exposed from this module.

Naming rule:

- File/module uses underscores (`my_package.py`).
- CLI arguments may use hyphens (`my-package`).

## Component Isolation Rules

When using `dependencies_dir` components:

- Keep components separated.
- Do not create cross-component imports unless explicitly intended and packaged.
- Do not wire package assembly through random files; wire through `module_dir/<package_name>.py`.

Main module should orchestrate components and imports.

## Recommended Pattern: attrsx + Composition

For multi-component packages, recommend `attrsx`:

- logger injection,
- handler wiring via declarative specs,
- clearer orchestration from the main module.

PAA works best when components are composable and main module acts as integration point (multiple-inheritance/composition style), rather than deep component-to-component coupling.

## Build and Validation Workflow

Preferred local validation command:

```bash
paa test-install <package-name>
```

Useful flags:

- `--skip-deps-install`
- `--build-mkdocs`
- `--keep-temp-files`
- `--check-full-deps-compat`

Use these to speed iteration and debug packaging outputs.

## Pattern-Break Inspection Checklist

When reviewing a user-created package, check for:

1. Missing/invalid `__package_metadata__`.
2. Main package module absent or misnamed.
3. Package logic not routed through `module_dir/<package_name>.py`.
4. Components importing each other in brittle ways.
5. Local dependencies not referenced by main module.
6. Optional files placed in wrong directories (`cli`, `api_routes`, `streamlit`, docs paths).
7. Inconsistent underscore/hyphen naming between files and CLI usage.

If issues are found, provide:

- exact file/path causing break,
- expected pattern,
- minimal correction steps,
- command to re-validate (`paa test-install ...`).

## Output Contract

For guidance tasks:

1. Show expected folder/file layout.
2. Provide concrete next command(s).
3. Highlight pattern-risk items early.

For review tasks:

1. List violations first (with paths).
2. Then provide minimal fix plan.
3. End with re-test command(s).
