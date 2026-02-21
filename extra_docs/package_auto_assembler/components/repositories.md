# Repositories and CI/CD Publishing

`package-auto-assembler` supports repository templates for automated package publishing.

For agent-oriented package guidance and extraction behavior, see `components/skills.md`.
For low-duplication docs strategy across README, MkDocs, and release notes, see `concepts/documentation_flow.md`.

## Supported Repository Modes

- **GitHub template**: CI/CD pipeline for packaging and publishing to **PyPI**.
- **Azure DevOps template**: CI/CD pipeline for packaging and publishing to **Azure Artifacts**.

Initialize templates with:

```bash
paa init-ppr --github
# or
paa init-ppr --azure
```

Use `--full` if you want full `.paa.config` template with all optional fields visible.

## Init Behavior (Config + Structure)

Current initialization flow is intentionally staged:

1. `paa init-ppr --<platform>` initializes workflow template files (`.github` or `.azure`).
2. If `.paa.config` is missing, it is created on that first run.
3. To initialize directories from config, run either:
   - `paa init-ppr --<platform>` again, or
   - `paa init-paa`.

This allows config to appear first and then be used to build directory structure.

## How CI/CD Chooses Package and Version

Publishing flow takes package context from commit messages.

Required package tag format:

- `[package_name] ...`

Only one package context per merge is recommended, because pipeline logic assumes a single package target.

## Versioning Model

PAA uses semantic versioning:

- `major.minor.patch`

Default increment behavior is **patch** unless commit message signals otherwise.

Version control tags:

- `[<package name>][..+]` -> patch
- `[<package name>][.+.]` -> minor
- `[<package name>][+..]` -> major
- `[<package name>][1.2.3]` -> force exact version

Version source behavior:

- PAA attempts to read latest version from package storage.
- If unavailable, it falls back to tracking logs in `.paa/tracking`.

## Automatic Release Notes from Commit Messages

Release notes are generated automatically as part of packaging/release flow.
PAA assembles notes from commit history using package tags:

- Commit messages with `[<package name>]` are collected.
- `;` splits one commit message into multiple note items.
- Previous release notes are used as boundary so only new relevant history is included.

First-release caveat:

- In a fresh repository, release-note extraction may be limited if merge-history context is sparse.

## GitHub Template Extras

Compared to the base publish flow, the GitHub template typically includes:

- **GitHub Pages docs support** via `gh-pages` workflow path and `gh_pages_base_url` config usage.
- **Tox-oriented PR validation flow** for test/lint checks before merge.

These extras are part of why `init-ppr --github` can be useful even before package publishing is enabled.

## Commit Message Examples

Patch (default style):

```text
[my_package][..+] fix parser edge case; improve log message
```

Minor:

```text
[my_package][.+.] add new extraction mode; expose cli flag
```

Major:

```text
[my_package][+..] refactor public API; remove deprecated route helpers
```

Explicit version:

```text
[my_package][2.3.0] align release with external service rollout
```

Package-only tag (still valid package targeting, default patch behavior):

```text
[my_package] fix docs typo; add missing test note
```
