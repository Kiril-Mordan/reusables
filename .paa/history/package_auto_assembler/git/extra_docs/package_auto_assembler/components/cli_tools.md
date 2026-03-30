
## About

One of available interfaces to use PAA capabalities is cli tools. After installing [`package-auto-assembler`](https://kiril-mordan.github.io/reusables/package_auto_assembler/) one can view the list of available cli tools like shown below.

``` bash
paa --help
```

``` bash
Usage: paa [OPTIONS] COMMAND [ARGS]...

  Package Auto Assembler CLI tool.

Options:
  --help  Show this message and exit.

Commands:
  add-mcp                      Register package MCP module in codex/claude...
  checkpoint-create            Create a package checkpoint in internal...
  checkpoint-list              List package checkpoints from internal...
  checkpoint-prune             Prune local checkpoint history.
  checkpoint-show              Show details for a specific checkpoint...
  cleanup-agent-skills         Clean PAA-managed skills from .agents/.claude...
  checkout                     Checkout package checkpoint.
  check-deps-compat            Check compatibility of declared dependency...
  check-licenses               Check licenses of the module.
  check-vulnerabilities        Check vulnerabilities of the module.
  convert-drawio-to-png        Converts drawio file to .png
  extract-module-artifacts     Extracts artifacts from packaged module.
  extract-module-mcp           Extract MCP module from packages that have it...
  extract-module-pyproject     Extracts package pyproject metadata from...
  extract-module-requirements  Extract module requirements.
  extract-module-routes        Extracts routes for fastapi from packages...
  extract-module-site          Extracts static mkdocs site from packaged...
  extract-module-streamlit     Extracts streamlit from packages that have...
  extract-skill                Extract a single skill from an installed...
  extract-skills               Extract all skills from an installed package.
  extract-tracking-version     Get latest package version.
  init-config                  Initialize config file
  init-api-config              Initialize API run config file.
  init-api                     Create API routes scaffold for a package in...
  init-cli                     Create CLI scaffold for a package in PPR.
  init-streamlit-config        Initialize Streamlit run config file.
  init-streamlit               Create Streamlit scaffold for a package in PPR.
  init-mcp-config              Initialize MCP run config file.
  init-mcp                     Create MCP module scaffold for a package in...
  init-paa                     Initialize paa tracking files and...
  init-ppr                     Initialize ppr for a given workflows...
  make-package                 Package with package-auto-assembler.
  refresh-module-artifacts     Refreshes module artifact from links.
  remove-package               Remove paa package from ppr
  rename-package               Rename paa package in ppr
  run-api-routes               Run fastapi with provided routes.
  run-mcp                      Run MCP application from package or filepath.
  run-pylint-tests             Run pylint tests for a given module, file,...
  run-streamlit                Run streamlit application from the package.
  show-module-artifacts        Shows module artifacts.
  show-module-artifacts-links  Shows module artifact links.
  show-module-info             Shows module info.
  show-module-licenses         Shows module licenses.
  show-module-list             Shows module list.
  show-module-mcp              Show MCP module availability and registered...
  show-module-requirements     Shows module requirements.
  show-ref-local-deps          Shows paths to local dependencies...
  test-install                 Test install module into local environment.
  unfold-package               Unfold paa package inside ppr
  update-release-notes         Update release notes.
```

Available cli tools usually employ multiple internal components and range from relatively simple ones to more complex.
For interface-level guidance on package CLI module layout and imports, see `interfaces/cli.md`.

## Description of tools

### Initializing PAA

Creating config file could be useful to avoid providing parameters manually. If no config file will be provided, by default values from `.paa.config` will be used.

``` bash
paa init-config  --help
```

``` bash
Usage: paa init-config [OPTIONS]

  Initialize config file

Options:
  --full  If checked, dirs beyond essential would be mapped.
  --help  Show this message and exit.
```

MCP hosting config scaffold can be initialized separately:

``` bash
paa init-mcp-config --help
```

``` bash
Usage: paa init-mcp-config [OPTIONS]

  Initialize MCP run config file.

Options:
  --config TEXT  Path to mcp config scaffold file.  [default: .paa.mcp.config]
  --force        If checked, existing mcp config will be overwritten.
  --help         Show this message and exit.
```

FastAPI run config scaffold can be initialized separately:

``` bash
paa init-api-config --help
```

``` bash
Usage: paa init-api-config [OPTIONS]

  Initialize API run config file.

Options:
  --config TEXT  Path to api config scaffold file.  [default: .paa.api.config]
  --force        If checked, existing api config will be overwritten.
  --help         Show this message and exit.
```

API routes scaffold can be initialized separately:

``` bash
paa init-api --help
```

``` bash
Usage: paa init-api [OPTIONS] MODULE_NAME

  Create API routes scaffold for a package in PPR.

Options:
  --config TEXT  Path to config file for paa.  [default: .paa.config]
  --force        If checked, overwrite existing api routes module.
  --help         Show this message and exit.
```

CLI scaffold can be initialized separately:

``` bash
paa init-cli --help
```

``` bash
Usage: paa init-cli [OPTIONS] MODULE_NAME

  Create CLI scaffold for a package in PPR.

Options:
  --config TEXT  Path to config file for paa.  [default: .paa.config]
  --force        If checked, overwrite existing cli module.
  --help         Show this message and exit.
```

Streamlit config scaffold can be initialized separately:

``` bash
paa init-streamlit-config --help
```

``` bash
Usage: paa init-streamlit-config [OPTIONS]

  Initialize Streamlit run config file.

Options:
  --config TEXT  Path to streamlit config scaffold file.  [default:
                 .paa.streamlit.config]
  --force        If checked, existing streamlit config will be overwritten.
  --help         Show this message and exit.
```

Streamlit app scaffold can be initialized separately:

``` bash
paa init-streamlit --help
```

``` bash
Usage: paa init-streamlit [OPTIONS] MODULE_NAME

  Create Streamlit scaffold for a package in PPR.

Options:
  --config TEXT  Path to config file for paa.  [default: .paa.config]
  --force        If checked, overwrite existing streamlit module.
  --help         Show this message and exit.
```

Packaging repository needs a place to keep some tracking files.
Running it first time also initializes `.paa.config` and the second time
will create directories specified there, if not already created.  

``` bash
paa init-paa  --help
```

``` bash
Usage: paa init-paa [OPTIONS]

  Initialize paa tracking files and directores from .paa.config

Options:
  --full  If checked, dirs beyond essential would be mapped.
  --help  Show this message and exit.
```

`init-paa` runs in two steps:

1. If `.paa.config` is missing, it is created first and command exits.
2. On the next run, directories are initialized from config values, with runtime defaults used for omitted path keys.

The package provides some templates for packaging repositories. Packaging repository after some additional preparations should allow to create and publish new packages with a use of ci/cd pipeline. 

``` bash
paa init-ppr --help
```

``` bash
Usage: paa init-ppr [OPTIONS]

  Initialize ppr for a given workflows platform.

Options:
  --github  If checked, git actions template would be set up.
  --azure   If checked, azure devops pipelines template would be set up.
  --full    If checked, dirs beyond essential would be mapped.
  --help    Show this message and exit.
```

`init-ppr` requires selecting a platform (`--github` or `--azure`).

On first run with selected platform:
- workflow templates are initialized (`.github` or `.azure`);
- `.paa.config` is also initialized if missing.

To initialize directories from config after that, run either:
- `paa init-ppr --<selected-platform>` again, or
- `paa init-paa`.

For a full field reference of `.paa.config`, see:
- `extra_docs/package_auto_assembler/components/.paa.config.md`

### Creating packages

Installing packages for a test in local environments could be a useful step to make sure everything works as expected before pushing changes to publishing repo. This creates an instance of the package in local environment with default version, with a greatly simplified building process that avoids making documentation, versioning and so on.

``` bash
paa test-install [OPTIONS] MODULE_NAME
```

``` bash
Usage: paa test-install [OPTIONS] MODULE_NAME

  Test install module into local environment.

Options:
  --config TEXT                   Path to config file for paa.
  --module-filepath TEXT          Path to .py file to be packaged.
  --mapping-filepath TEXT         Path to .json file that maps import to
                                  install dependecy names.
  --cli-module-filepath TEXT      Path to .py file that contains cli logic.
  --fastapi-routes-filepath TEXT  Path to .py file that routes for fastapi.
  --dependencies-dir TEXT         Path to directory with local dependencies of
                                  the module.
  --default-version TEXT          Default version.
  --check-vulnerabilities         If checked, checks module dependencies with
                                  pip-audit for vulnerabilities.
  --skip-deps-compat-check        If checked, skips dependency compatibility
                                  check.
  --check-full-deps-compat        If checked, runs full dependency resolver
                                  compatibility check.
  --build-mkdocs                  If checked, builds mkdocs documentation.
  --check-licenses                If checked, checks module dependencies
                                  licenses.
  --keep-temp-files               If checked, setup directory won't be removed
                                  after setup is done.
  --skip-deps-install             If checked, existing dependencies from env
                                  will be reused.
  --checkpoint                    If checked, creates checkpoint before package
                                  build/install.
  --help                          Show this message and exit.
```

Checkpoint behavior for `test-install`:
- Default: no checkpoint.
- Use `--checkpoint` to store a checkpoint for the tested state.
- The checkpoint version label uses effective run version (usually `0.0.0` unless overridden).

Making package based on provided parameters can be useful in ci/cd pipelines to streamline creation of packages before publishing from something that could be as simple as `.py` file.

``` bash
paa make-package --help
```

``` bash
Usage: paa make-package [OPTIONS] MODULE_NAME

  Package with package-auto-assembler.

Options:
  --config TEXT                   Path to config file for paa.
  --module-filepath TEXT          Path to .py file to be packaged.
  --mapping-filepath TEXT         Path to .json file that maps import to
                                  install dependecy names.
  --cli-module-filepath TEXT      Path to .py file that contains cli logic.
  --fastapi-routes-filepath TEXT  Path to .py file that routes for fastapi.
  --dependencies-dir TEXT         Path to directory with local dependencies of
                                  the module.
  --kernel-name TEXT              Kernel name.
  --python-version TEXT           Python version.
  --default-version TEXT          Default version.
  --ignore-vulnerabilities-check  If checked, does not check module
                                  dependencies with pip-audit for
                                  vulnerabilities.
  --skip-deps-compat-check        If checked, skips dependency compatibility
                                  check.
  --skip-full-deps-compat-check   If checked, skips full dependency resolver
                                  compatibility check.
  --ignore-licenses-check         If checked, does not check module licenses
                                  for unexpected ones.
  --example-notebook-path TEXT    Path to .ipynb file to be used as README.
  --execute-notebook              If checked, executes notebook before turning
                                  into README.
  --log-filepath TEXT             Path to logfile to record version change.
  --versions-filepath TEXT        Path to file where latest versions of the
                                  packages are recorded.
  --no-checkpoint                 If checked, skips checkpoint creation before
                                  package build.
  --help                          Show this message and exit.
```

Checkpoint behavior for `make-package`:
- Default: checkpoint is created.
- Use `--no-checkpoint` to skip checkpoint creation.
- Packaged checkpoint history is automatically pruned to exclude `0.0.0` checkpoints.

### Execution flows

The following summarizes what happens internally for the main packaging commands.

#### make-package flow

1. Load `.paa.config` and resolve package-specific paths.
2. Initialize `PackageAutoAssembler` with packaging, docs, artifacts, and validation settings.
3. Read metadata from module/CLI and calculate version (plus release notes when enabled).
4. Prepare setup directory and merge local dependencies.
5. Extract requirements from module, CLI, API routes, and streamlit sources.
6. Build docs inputs (README/extra docs/mkdocs).
7. Create checkpoint by default (unless `--no-checkpoint`).
8. Export pruned checkpoint history for packaging (drop `0.0.0` checkpoints).
9. Collect artifacts and build package files (`setup.py` + distribution artifacts).

#### test-install flow

1. Load `.paa.config` and resolve package-specific paths.
2. Initialize `PackageAutoAssembler` for local build/install flow.
3. Read metadata and assign default version.
4. Prepare setup directory and merge local dependencies.
5. Extract requirements from module, CLI, API routes, and streamlit sources.
6. Optionally build mkdocs, then prepare artifacts and setup file.
7. Optionally create checkpoint when `--checkpoint` is provided.
8. Build package and install it into current environment.
9. Remove temporary setup directory unless `--keep-temp-files` is set.

#### check-deps-compat flow

1. Load `.paa.config` and resolve package paths.
2. Initialize `PackageAutoAssembler` in compatibility-check mode.
3. Prepare temporary setup directory and resolve effective requirements.
4. Run static constraint compatibility check.
5. Optionally run full resolver check when `--full` is provided.
6. Print pass/fail status and clean temporary setup directory.

#### Compatibility defaults

| Command | Static check | Full resolver check |
|---|---|---|
| `paa make-package` | enabled by default | enabled by default |
| `paa test-install` | enabled by default | disabled by default |
| `paa check-deps-compat` | enabled | optional (`--full`) |


### History flow

This section summarizes how checkpoint history is stored, created, packaged, and restored.

Where history lives:
- Local unfolded history: `.paa/history/<package>/git`
- Packaged history payload: `.paa.tracking/git` (work tree) and `.paa.tracking/git_repo` (git metadata)

History creation:
- Manual: `paa checkpoint-create <package>`
- Test install: `paa test-install <package> --checkpoint` (optional)
- Make package: `paa make-package <package>` (default unless `--no-checkpoint`)

History packaging behavior:
- `make-package` exports a pruned checkpoint history for packaged artifacts.
- By default, checkpoints with version `0.0.0` are excluded from packaged history.
- Local history is not modified by this packaging-time pruning.
- To prune local history explicitly, use `paa checkpoint-prune`.

History restore and usage:
- `paa checkpoint-list` / `paa checkpoint-show` read available checkpoint history from package context.
- `paa checkout` restores selected checkpoint content.
- Default checkout target is latest stable tag (`vX.Y.Z`); use explicit `dev-latest` or commit hash when needed.

History maintenance:
- `paa checkpoint-prune <package>` defaults to pruning `0.0.0` checkpoints.
- `--dry-run` previews prune effect.
- `--version <x.y.z>` prunes specific version checkpoints.
- `--commit <sha_prefix>` prunes a specific checkpoint commit.

Typical sequence:

``` bash
# 1) Create local dev checkpoint(s)
paa checkpoint-create package-auto-assembler

# 2) Build package (checkpoint created by default; packaged history prunes 0.0.0)
paa make-package package-auto-assembler

# 3) Inspect history
paa checkpoint-list package-auto-assembler

# 4) Restore explicit checkpoint into unfolded files only
paa checkout package-auto-assembler dev-latest --unfold --no-install
```


#### Creating checkpoints

Use `checkpoint-create` for explicit/manual checkpoints.

``` bash
paa checkpoint-create --help
```

``` bash
Usage: paa checkpoint-create [OPTIONS] MODULE_NAME

  Create a package checkpoint in internal history store.

Options:
  --version-label TEXT  Version label to tag checkpoint with.  [default:
                        0.0.0]
  --source-event TEXT   Source event label recorded in checkpoint commit
                        message.  [default: manual]
  --help                Show this message and exit.
```

Examples:

``` bash
# Manual dev checkpoint
paa checkpoint-create package-auto-assembler

# Explicit version checkpoint
paa checkpoint-create package-auto-assembler --version-label 1.2.3 --source-event release
```

#### Navigating and inspecting history

Use `checkpoint-list` to navigate available checkpoints and `checkpoint-show` for details.

``` bash
paa checkpoint-list package-auto-assembler
paa checkpoint-show package-auto-assembler dev-latest
```

``` bash
paa checkpoint-list --help
```

``` bash
Usage: paa checkpoint-list [OPTIONS] MODULE_NAME

  List package checkpoints from internal history store.

Options:
  --limit INTEGER  Maximum number of checkpoints to list.  [default: 20]
  --help           Show this message and exit.
```

#### Checking out previous versions

Checkout target resolution:
- Default `paa checkout <package>` looks for latest stable tag (`vX.Y.Z`).
- If stable tags are not present, use explicit target such as `dev-latest` or commit hash.

Checkout behavior:
- Default checkout applies target state in a temporary workspace and runs `test-install` from there; unfolded files are not changed.
- `--unfold` additionally syncs the checked-out state into unfolded package files in current workspace.
- `--no-install` skips the reinstall step.
- `--unfold --no-install` updates unfolded files only (no reinstall).

Checkout change summary:
- `written`: files created in unfolded package scope.
- `updated`: existing files overwritten to match checkpoint target.
- `deleted`: package-scoped files removed because they are absent in checkpoint target.

Examples:

``` bash
# Preview planned checkout changes
paa checkout package-auto-assembler dev-latest --dry-run --unfold --no-install

# Apply only to unfolded files (no reinstall)
paa checkout package-auto-assembler dev-latest --unfold --no-install

# Apply and reinstall from checked-out temp workspace
paa checkout package-auto-assembler dev-latest
```

#### Pruning history

Use `checkpoint-prune` to remove old or specific checkpoints from local history.

``` bash
paa checkpoint-prune --help
```

``` bash
Usage: paa checkpoint-prune [OPTIONS] MODULE_NAME

  Prune local checkpoint history.

Options:
  --commit TEXT   Specific checkpoint commit (or prefix) to remove.
  --version TEXT  Remove checkpoints for a specific version label.
  --dry-run       Show what would be pruned without changing history.
  --help          Show this message and exit.
```

Examples:

``` bash
# Default prune behavior: remove checkpoints with version=0.0.0
paa checkpoint-prune package-auto-assembler

# Preview prune effect without modifying history
paa checkpoint-prune package-auto-assembler --dry-run

# Remove checkpoints for a specific version
paa checkpoint-prune package-auto-assembler --version 0.1.2

# Remove one specific checkpoint commit
paa checkpoint-prune package-auto-assembler --commit 03aa890
```


### Working with packages within PAA

Published packages could be installed and unfolded for editing anywhere, given that they are independent of a packaging repositories and enviroment that produced them.

``` bash
paa unfold-package --help
```

``` bash
Usage: paa unfold-package [OPTIONS] MODULE_NAME

  Unfold paa package inside ppr

Options:
  --debug  If checked, debug messages will be shown.
  --help   Show this message and exit.
```

Since packaging repository is just a workbench, ability to remove packages that no longer being published there could be useful. 

``` bash
paa remove-package --help
```

``` bash
Usage: paa remove-package [OPTIONS] MODULE_NAME

  Remove paa package from ppr

Options:
  --debug  If checked, debug messages will be shown.
  --help   Show this message and exit.
```

Ability to unfold packages created with `package-auto-assembler`, paired with a method to rename them, would allow to fork the package and start publishing it in the same package storage, just under different name.

``` bash
paa rename-package --help
```

``` bash
Usage: paa rename-package [OPTIONS] MODULE_NAME NEW_MODULE_NAME

  Rename paa package in ppr

Options:
  --debug  If checked, debug messages will be shown.
  --help   Show this message and exit.
```



### Checking dependencies

Checking vulnerabilities with `pip-audit` is usefull. This checks vulnerabilities of .py files and its local dependencies with `pip-audit`.

``` bash
paa check-vulnerabilities --help
```

``` bash
Usage: paa check-vulnerabilities [OPTIONS] MODULE_NAME

  Check vulnerabilities of the module.

Options:
  --config TEXT               Path to config file for paa.
  --module-filepath TEXT      Path to .py file to be packaged.
  --mapping-filepath TEXT     Path to .json file that maps import to install
                              dependecy names.
  --cli-module-filepath TEXT  Path to .py file that contains cli logic.
  --dependencies-dir TEXT     Path to directory with local dependencies of the
                              module.
  --help                      Show this message and exit.
```

Checking compatibility of dependency constraints can be done separately as a dedicated CLI call.

``` bash
paa check-deps-compat --help
```

``` bash
Usage: paa check-deps-compat [OPTIONS] MODULE_NAME

  Check compatibility of declared dependency constraints for the module.

Options:
  --config TEXT               Path to config file for paa.
  --module-filepath TEXT      Path to .py file to be packaged.
  --mapping-filepath TEXT     Path to .json file that maps import to install
                              dependecy names.
  --cli-module-filepath TEXT  Path to .py file that contains cli logic.
  --dependencies-dir TEXT     Path to directory with local dependencies of the
                              module.
  --full                      If checked, runs full dependency resolver
                              compatibility check.
  --help                      Show this message and exit.
```

Compatibility defaults by command:
- `paa make-package`: static and full compatibility checks run by default. Use `--skip-deps-compat-check` and/or `--skip-full-deps-compat-check` to disable.
- `paa test-install`: static compatibility check runs by default, full resolver check is off by default. Use `--check-full-deps-compat` to enable full resolver check.

When compatibility fields in `.paa.config` are omitted or set to `null`, command defaults above are used.

Checking license labels of module dependencies tree could be useful to prevent using some dependencies early on.

``` bash
Usage: paa check-licenses [OPTIONS] MODULE_NAME

  Check licenses of the module.

Options:
  --config TEXT                   Path to config file for paa.
  --module-filepath TEXT          Path to .py file to be packaged.
  --mapping-filepath TEXT         Path to .json file that maps import to
                                  install dependecy names.
  --license-mapping-filepath TEXT
                                  Path to .json file that maps license labels
                                  to install dependecy names.
  --cli-module-filepath TEXT      Path to .py file that contains cli logic.
  --dependencies-dir TEXT         Path to directory with local dependencies of
                                  the module.
  --skip-normalize-labels         If checked, package license labels are not
                                  normalized.
  --help                          Show this message and exit.
```

### Running apps from packages

Packaging process could help building APIs as well. This package would call routes stored within other packages and routes stored in files to form one application, so that repeatable structure does not need to copied between projects, but instead built in one places and extended with some config files in many. Since routes are python code that can have its dependencies, it makes sense to store them within packages sometimes to take advantage of automated dependency handling and import code straight from the package, eliminating in turn situation when package release in no compatible anymore with routes based on them. 

Parameters for fastapi app description, middleware and run could be supplied via optional `.paa.api.config` file, with `DESCRIPTION` , `MIDDLEWARE` and `RUN` dictionary of parameters respectively. 

It could be beneficial to add a static page with documentation, so additional pages could be addded. First one would be accessible via `\mkdocs` and the following ones via `\mkdocs {i+1}`. Static package within package, that were packages by `package-auto-assemble>0.5.1` would be accessible via `\{package_name}\docs` if available.

``` bash
paa run-api-routes --help
```

``` bash
Usage: paa run-api-routes [OPTIONS]

  Run fastapi with provided routes.

Options:
  --api-config TEXT  Path to yml config file with app description, middleware
                     parameters, run parameters, `.paa.api.config` is used by
                     default.
  --host TEXT        The host to bind to.
  --port TEXT        The port to bind to.
  --package TEXT     Package names from which routes will be added to the app.
  --route TEXT       Paths to routes which will be added to the app.
  --docs TEXT        Paths to static docs site which will be added to the app.
  --help             Show this message and exit.
```

For detailed FastAPI interface workflows, see `interfaces/fastapi.md`.


One of the convinient ways to access packaged code could be a streamlit application. This package allows for streamlit application to be stored within a package and then run with the following. Parameters that would be passed to `~/.streamlit/config.toml` can be provided via optional `.paa.streamlit.config` file, at which point it would copied to default location. The command can be used to run streamlit apps from a selected package, built with the tool, or from normal `.py` file with streamlit app.

``` bash
paa run-streamlit --help
```

``` bash
Usage: paa run-streamlit [OPTIONS]

  Run streamlit application from the package.

Options:
  --app-config TEXT  Path to yml config for streamlit app.
  --host TEXT        The host to bind to.
  --port TEXT        The port to bind to.
  --package TEXT     Package name from which streamlit app should be run.
  --path TEXT        Path to streamlit app.
  --help             Show this message and exit.
```

For detailed Streamlit interface workflows, see `interfaces/streamlit.md`.

### MCP tools

PAA supports MCP module scaffolding, package extraction, local execution, and agent registration.

``` bash
paa init-mcp --help
```

``` bash
Usage: paa init-mcp [OPTIONS] MODULE_NAME

  Create MCP module scaffold for a package in PPR.

Options:
  --config TEXT            Path to config file for paa.
  --module-name TEXT       Module name if different from argument label.
  --mcp-module-filepath TEXT
                           Path to .py file for MCP module.
  --force                  If checked, overwrite existing MCP module.
  --help                   Show this message and exit.
```

``` bash
paa add-mcp --help
```

``` bash
Usage: paa add-mcp [OPTIONS] MODULE_NAME

  Register package MCP module in codex/claude client.

Options:
  --target [codex|claude]  Agent target for MCP registration.
  --python-path TEXT       Python interpreter to run MCP module with.
  --server-name TEXT       Optional MCP server name override.
  --help                   Show this message and exit.
```

Notes:
- `add-mcp` registers MCP from installed package files.
- If no installed MCP module is found for selected package, command fails.

Example:

``` bash
paa add-mcp your-package-1 --target codex --python-path /path/to/your/python
```

Flag guidance:
- `--target` is optional when auto-detection resolves a single target.
- `--python-path` is optional if default `python` points to desired environment.
- `--server-name` is optional unless you need a custom server ID in client config.

``` bash
paa show-module-mcp --help
```

``` bash
Usage: paa show-module-mcp [OPTIONS] LABEL_NAME

  Show MCP module availability and registered tool list for an installed
  package.

Options:
  --tools  If checked, inspect and show registered tool names.
  --help   Show this message and exit.
```

``` bash
paa run-mcp --help
```

``` bash
Usage: paa run-mcp [OPTIONS]

  Run hosted MCP application(s) from package(s) and/or filepath(s).

Options:
  --mcp-config TEXT               Path to yml config file with MCP run settings and sources.
  --package TEXT                  Package names from which MCP app should be run.
  --path TEXT                     Path(s) to MCP module file.
  --host TEXT                     Host to bind MCP server to.
  --port INTEGER                  Port to bind MCP server to.
  --transport [sse|streamable-http]
                                  Hosted MCP transport mode.
  --mount-path TEXT               Optional mount path for SSE transport.
  --mode [split|combine]          Run mode for MCP hosting.
  --server-prefix TEXT            Server name prefix. In split mode used only
                                  when explicitly provided.
  --help                          Show this message and exit.
```

`run-mcp` source selection can come from flags (`--package`, `--path`) and/or `.paa.mcp.config`:

```yaml
RUN:
  host: "0.0.0.0"
  port: 8000
  transport: "streamable-http"
  mount_path: null
  mode: "split"
  server_prefix: null

SOURCES:
  packages:
    - your-package-1
    - your-package-2
  paths: []
```

Mode and naming behavior:
- `split` (default): one server per source.
- `combine`: one server for all sources.
- In `split`, default naming has no prefix; prefix is applied only when explicitly provided (`--server-prefix` or config `RUN.server_prefix`).
- In `combine`, server name defaults to `paa-http` unless overridden.

For detailed MCP workflows, see `interfaces/mcp.md`.

`run-mcp` flag guidance:
- if `.paa.mcp.config` exists, command can run without explicit source flags.
- `--host` / `--port` only needed for non-default bind settings.
- `--mode` defaults to `split`.
- in `split`, `--server-prefix` is optional and applied only when explicitly set.

``` bash
paa extract-module-mcp --help
```

``` bash
Usage: paa extract-module-mcp [OPTIONS] PACKAGE_NAME

  Extract MCP module from packages that have it into a file.

Options:
  --output-dir TEXT   Directory where MCP module extracted from the package
                      will be copied to.
  --output-path TEXT  Filepath to which MCP module extracted from the package
                      will be copied to.
  --help              Show this message and exit.
```

### Extracting files from packages

Storing routes within package could be convinient, but extracting them from a package is not. To mitigate that, the following exists to extract `routes.py` from a package that contains it.

``` bash
paa extract-module-routes --help
```

``` bash
Usage: paa extract-module-routes [OPTIONS] PACKAGE_NAME

  Extracts routes for fastapi from packages that have them into a file.

Options:
  --output-dir TEXT   Directory where routes extracted from the package will
                      be copied to.
  --output-path TEXT  Filepath to which routes extracted from the package will
                      be copied to.
  --help              Show this message and exit.
```

``` bash
paa extract-module-site --help
```

``` bash
Usage: paa extract-module-site [OPTIONS] PACKAGE_NAME

  Extracts static mkdocs site from packaged module.

Options:
  --output-dir TEXT   Directory where routes extracted from the package will
                      be copied to.
  --output-path TEXT  Filepath to which routes extracted from the package will
                      be copied to.
  --help              Show this message and exit.
```

Another option to access the artifacts is to copy them to a selected directory.

``` bash
paa extract-module-artifacts --help
```

``` bash
Usage: paa extract-module-artifacts [OPTIONS] PACKAGE_NAME

  Extracts artifacts from packaged module.

Options:
  --artifact TEXT     Name of the artifact to be extracted.
  --output-dir TEXT   Directory where artifacts extracted from the package
                      will be copied to.
  --output-path TEXT  Filepath to which artifact extracted from the package
                      will be copied to.
  --help              Show this message and exit.
```

Another option to access the packaged streamlit app is to copy it to a selected directory.

``` bash
paa extract-module-streamlit --help
```

``` bash
Usage: paa extract-module-streamlit [OPTIONS] PACKAGE_NAME

  Extracts streamlit from packages that have them into a file.

Options:
  --output-dir TEXT   Directory where streamplit extracted from the package
                      will be copied to.
  --output-path TEXT  Filepath to which streamlit extracted from the package
                      will be copied to.
  --help              Show this message and exit.
```

To make package metadata directly reusable with `uv`/`poetry`, pyproject can be extracted from installed package tracking files, or generated in poetry style.

``` bash
paa extract-module-pyproject --help
```

``` bash
Usage: paa extract-module-pyproject [OPTIONS] PACKAGE_NAME

  Extracts package pyproject metadata from installed package tracking.

Options:
  --format [pep621|uv|poetry]  Output format for extracted pyproject.
                               [default: pep621]
  --output-dir TEXT            Directory where extracted pyproject will be
                               copied/generated.
  --output-path TEXT           Filepath where extracted pyproject will be
                               copied/generated.
  --help                       Show this message and exit.
```

By default, the command writes to `./pyproject.toml`, which can be used directly by tools like `uv` and `poetry`.

``` bash
paa extract-module-pyproject package_auto_assembler --format uv
paa extract-module-pyproject package_auto_assembler --format poetry --output-path ./pyproject.toml
```

PAA can also extract packaged agent skills.

``` bash
paa extract-skill --help
```

``` bash
Usage: paa extract-skill [OPTIONS] PACKAGE_NAME SKILL_NAME

  Extract a single skill from an installed package.

Options:
  --target [codex|claude]  Agent target for auto-detected output path.
  --output-dir TEXT        Destination skills root. If omitted, target path is
                           auto-detected.
  --help                   Show this message and exit.
```

``` bash
paa extract-skills --help
```

``` bash
Usage: paa extract-skills [OPTIONS] PACKAGE_NAME

  Extract all skills from an installed package.

Options:
  --target [codex|claude]  Agent target for auto-detected output path.
  --output-dir TEXT        Destination skills root. If omitted, target path is
                           auto-detected.
  --help                   Show this message and exit.
```

Auto-detection behavior for skill extraction:
- If `--output-dir` is provided, it is used directly.
- Otherwise PAA searches upward from the current directory and detects target roots from markers (`.agents`/`.claude`, `AGENTS.md`/`CLAUDE.md`).
- If both targets are detected, provide `--target` or `--output-dir`.
- If no target markers are found, PAA defaults to user-level codex path: `~/.agents/skills`.

Examples:

``` bash
paa extract-skill package_auto_assembler dependency-management-audit --target codex
paa extract-skills package_auto_assembler --target claude
```

### Agent skills maintenance

Installed skills extracted by PAA include a small marker (`.paa_skill_meta.yml`), enabling safe cleanup of only PAA-managed entries.

``` bash
paa cleanup-agent-skills --help
```

``` bash
Usage: paa cleanup-agent-skills [OPTIONS]

  Clean PAA-managed skills from .agents/.claude skills root.

Options:
  --target [codex|claude]  Agent target for auto-detected output path.
  --output-dir TEXT        Skills root to clean. If omitted, target path is
                           auto-detected.
  --help                   Show this message and exit.
```

``` bash
paa cleanup-agent-skills --target codex
```


### Show modules info

Cli interface provides some additional tools to analyse locally installed packages if they were build with package-auto-assembler>0.4.2. These include methods to list modules, show module info, extract requirements.

``` bash
paa show-module-list --help
```

```
Usage: paa show-module-list [OPTIONS]

  Shows module list.

Options:
  --tags TEXT  Keyword tag filters for the package.
  --help       Show this message and exit.
```


``` bash
paa show-module-info --help
```

``` bash
Usage: paa show-module-info [OPTIONS] LABEL_NAME

  Shows module info.

Options:
  --keywords      If checked, returns keywords for the package.
  --classifiers   If checked, returns classfiers for the package.
  --docstring     If checked, returns docstring of the package.
  --author        If checked, returns author of the package.
  --author-email  If checked, returns author email of the package.
  --version       If checked, returns installed version of the package.
  --pip-version   If checked, returns pip latest version of the package.
  --help          Show this message and exit.
```

``` bash
paa show-module-requirements --help
```

``` bash
Usage: paa show-module-requirements [OPTIONS] LABEL_NAME

  Shows module requirements.

Options:
  --help  Show this message and exit.
```

``` bash
paa show-module-licenses --help
```

``` bash
Usage: paa show-module-licenses [OPTIONS] PACKAGE_NAME

  Shows module licenses.

Options:
  --normalize-labels  If checked, package license labels are normalized.
  --help              Show this message and exit.
```

There is an option to package artifacts with the code. Packaged artifacts can be listed. 

``` bash
paa show-module-artifacts --help
```

``` bash
Usage: paa show-module-artifacts [OPTIONS] LABEL_NAME

  Shows module artifacts.

Options:
  --help  Show this message and exit.
```

It might be useful to inspect which artifacts come from links, whether these links are available and refresh these artifacts within installed package.

``` bash
paa show-module-artifacts-links --help
```

``` bash
Usage: paa show-module-artifacts-links [OPTIONS] LABEL_NAME

  Shows module artifact links.

Options:
  --help  Show this message and exit.
```

A module can referance multiple other local dependencies. The following is meant to extract all of paths relates to the module within PPR.

``` bash
paa show-ref-local-deps --help
```

``` bash
Usage: paa show-ref-local-deps [OPTIONS] LABEL_NAME

  Shows paths to local dependencies referenced in the module.

Options:
  --config TEXT            Path to config file for paa.
  --module-dir TEXT        Path to folder with .py file to be packaged.
  --dependencies-dir TEXT  Path to directory with local dependencies of
                           the module.
  --help                   Show this message and exit.
```

### Other

Some artifacts can come from links and there might be a need to refresh or even download these files (depending on how a link was provided). 

``` bash
paa refresh-module-artifacts --help
```

``` bash
Usage: paa refresh-module-artifacts [OPTIONS] LABEL_NAME

  Refreshes module artifact from links.

Options:
  --help  Show this message and exit.
```

Core of paa automation is the ability to extract requirements from `.py` files. The tool shown below is a part of requirements extraction pipeline, designed to run within PPR, but could also work outside, if imports are handled in a specific way (more in description).

``` bash
paa extract-module-requirements --help
```

``` bash
Usage: paa extract-module-requirements [OPTIONS] MODULE_NAME

  Extract module requirements.

Options:
  --config TEXT                   Path to config file for paa.
  --module-dir TEXT               Path to folder where module is stored.
  --mapping-filepath TEXT         Path to .json file that maps import to
                                  install dependecy names.
  --cli-module-filepath TEXT      Path to .py file that contains cli logic.
  --routes-module-filepath TEXT   Path to .py file that contains fastapi
                                  routes.
  --streamlit-module-filepath TEXT
                                  Path to .py file that contains streamlit
                                  app.
  --dependencies-dir TEXT         Path to directory with local dependencies of
                                  the module.
  --show-extra                    If checked, list will show which
                                  requirements are extra.
  --skip-extra                    If checked, list will not include extra.
  --help                          Show this message and exit.
```


Maintaining release notes could be very useful, but also tedious task. 
Since commit messages are rather standard practice, by taking advantage of them and constructing release notes based on them, each release could contain notes with appropriate version automatically, when itegrated into ci/cd pipeline, given that commit messages are written in a specific way. 

``` bash
paa update-release-notes --help
```

``` bash
Usage: paa update-release-notes [OPTIONS] LABEL_NAME

  Update release notes.

Options:
  --version TEXT           Version of new release.
  --notes TEXT             Optional manually provided notes string, where each
                           note is separated by ; and increment type is
                           provide in accordance to paa documentation.
  --notes-filepath TEXT    Path to .md wit release notes.
  --max-search-depth TEXT  Max search depth in commit history.
  --use-pip-latest         If checked, attempts to pull latest version from
                           pip.
  --help                   Show this message and exit.
```

Running pylint tests is useful and usually done in pull request to PPR. It could also be run locally for all the modules or select modules and their local dependencies to identify modules that need improvements to pass preset threshold. 

``` bash
paa run-pylint-tests --help
```

``` bash
Usage: paa run-pylint-tests [OPTIONS] [FILES]...

  Run pylint tests for a given module, file, files or files in a directory.

Options:
  --config TEXT      Path to config file for paa.
  --label-name TEXT  Label name.
  --module-dir TEXT  Path to a directory where .py files are stored.
  --threshold TEXT   Pylint threshold.
  --help             Show this message and exit.
```

It might be useful to know what is the last version a given module that was published from the PPR, mostly within ci/cd workflows.

``` bash
paa extract-tracking-version --help
```

``` bash
Usage: paa extract-tracking-version [OPTIONS] MODULE_NAME

  Get latest package version.

Options:
  --config TEXT  Path to config file for paa.
  --help         Show this message and exit.
```

Some pieces of documentation within PPR may come from drawio files. One of the steps in packaging process is to convert `.drawio` file for a package into `.png` files. 
For this functionality to work, first some dependencies would need to be installed.

``` bash
sudo apt-get update
sudo apt-get install -y wget xvfb libnotify4 libxml2-utils
wget https://github.com/jgraph/drawio-desktop/releases/download/v24.6.4/drawio-amd64-24.6.4.deb
sudo dpkg -i drawio-amd64-24.6.4.deb
sudo apt-get install -f
```

``` bash
paa convert-drawio-to-png --help
```

``` bash
Usage: paa convert-drawio-to-png [OPTIONS]

  Converts drawio file to .png

Options:
  --config TEXT      Path to config file for paa.
  --label-name TEXT  Label name.
  --drawio-dir TEXT  Path to a directory where drawio files are stored.
  --docs-dir TEXT    Path to the output directory for .png file.
  --help             Show this message and exit.
```

Before conversion, existing drawio-generated PNG files for the selected package are cleaned from docs output to remove stale tabs from removed/renamed drawio pages. Notebook-generated PNG files (for example `*_cell23_out0.png`) are preserved.
