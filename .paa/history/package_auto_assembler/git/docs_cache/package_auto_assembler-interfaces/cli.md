# CLI Interface

## About

PAA supports packaging package-specific CLI modules and exposing them through installed entrypoints.
The package CLI source is expected in `cli/<module_name>.py` (or configured `cli_dir`).
Core dependency used under the hood: [Click](https://click.palletsprojects.com/).
PAA expects one CLI file per package, with filename matching the package/module name.
For cross-component preflight checks before packaging, see `concepts/prepackaging_todo.md`.

## Quick Start

### 1. Initialize CLI scaffold for a package

```bash
paa init-cli your-package-1
```

This creates `cli/your_package_1.py` (or configured `cli_dir`).

### 2. Package and install

```bash
paa test-install your-package-1 --skip-deps-install
```

### 3. Run installed package CLI

Use the package entrypoint configured by that package (as defined in package metadata).
Metadata field details (including CLI naming interactions) are documented in `components/package_metadata.md`.

## Operational Commands

Initialize CLI scaffold:

```bash
paa init-cli your-package-1
```

Package/install and validate CLI wiring:

```bash
paa test-install your-package-1 --skip-deps-install
```

Inspect available package metadata and requirements:

```bash
paa show-module-info your-package-1
paa show-module-requirements your-package-1
```

## Python File Layout

### CLI module file

- path: `cli/<module_name>.py` (or configured `cli_dir`)
- expected structure:
  - `click` command group
  - one or more commands bound to the group
  - optional `if __name__ == "__main__":` runner for direct file execution

Recommended layout:

```python
import click
from your_package_1.your_package_1 import *

__cli_metadata__ = {
    "name": "your_package_1"
}


@click.group()
def cli():
    """CLI for your-package-1."""


@click.command()
@click.option("--name", default="world")
def ping(name: str):
    click.echo(f"pong: {name}")

cli.add_command(ping, "ping")


if __name__ == "__main__":
    cli()
```

For larger CLIs, explicit `cli.add_command(...)` registration is recommended to keep command wiring obvious.

### Optional CLI metadata

CLI module can define:

```python
__cli_metadata__ = {
    "name": "your_package_1"
}
```

`name` controls generated console script command name.
- default behavior (if metadata is omitted): package/module name without dashes
- override behavior: set `__cli_metadata__["name"]` to desired command label

## Importing From Package

Default import style for CLI modules:

- `from <package>.<package> import *`

Guidance:
- import from package namespace, not from PPR component file paths.
- keep CLI modules lightweight; call into package functions/classes rather than embedding heavy logic in CLI handlers.
- keep command names stable once users/scripts depend on them.

## Packaging Notes

During packaging, PAA copies package CLI module into installed package files as `cli.py`.
If no CLI module exists for a package, no package-specific CLI script is prepared.
Imports from the package CLI module are included in dependency extraction during packaging, similar to the main module.

## Notes

- Use `--help` on each command group for discoverability.
- Keep user-facing messages explicit and actionable for automation workflows.
