---
name: paa-checkpoint-history
description: Manage and navigate PAA checkpoint history (create, list, inspect, checkout, prune) with safe restore workflows.
---

# PAA Checkpoint History

Use this skill when users ask to inspect checkpoint history, restore a previous package state, create checkpoints, or prune checkpoint history.

## What This Skill Covers

- Creating checkpoints manually and from packaging flows.
- Listing and inspecting checkpoint history.
- Checking out previous package states safely.
- Pruning checkpoint history, including default dev-version pruning.

## History Model

- Local checkpoint history: `.paa/history/<package_name>/git`
- Packaged checkpoint payload:
  - `.paa.tracking/git` (history work tree)
  - `.paa.tracking/git_repo` (git metadata)

Packaged history is pruned during `make-package` to exclude `0.0.0` checkpoints by default.
Local history remains intact unless explicitly pruned.

## Core Commands

- `paa checkpoint-create <package> [--version-label X.Y.Z] [--source-event ...]`
- `paa checkpoint-list <package> [--limit N]`
- `paa checkpoint-show <package> [target]`
- `paa checkout <package> [target] [--dry-run] [--unfold] [--no-install]`
- `paa checkpoint-prune <package> [--dry-run] [--version X.Y.Z] [--commit <sha_prefix>]`

## Checkout Semantics

Default target behavior:

- `paa checkout <package>` resolves to latest stable `vX.Y.Z`.
- If no stable tag exists, use explicit `dev-latest` or commit hash.

Execution behavior:

- Default: restore in temp workspace + reinstall via `test-install`.
- `--unfold`: also sync checkpoint state into unfolded files.
- `--no-install`: skip reinstall.
- `--unfold --no-install`: unfolded sync only.

Change summary fields:

- `written`: new files created
- `updated`: existing files overwritten
- `deleted`: package-scoped files removed because absent in target checkpoint

## Safe Agent Procedure

1. Normalize package name (`-` and `_` as needed for CLI input).
2. Run `checkpoint-list` first.
3. If user asks to restore, run a dry run first:
   - `paa checkout <package> <target> --dry-run --unfold --no-install`
4. Explain intended effect (especially deleted file count).
5. Ask before applying install-changing checkout.
6. Use target mode based on user intent:
   - code only restore: `--unfold --no-install`
   - full env restore: default checkout

## Examples

```bash
# Create manual dev checkpoint
paa checkpoint-create package-auto-assembler

# Inspect history and one checkpoint
paa checkpoint-list package-auto-assembler
paa checkpoint-show package-auto-assembler dev-latest

# Restore code only (no reinstall)
paa checkout package-auto-assembler dev-latest --unfold --no-install

# Restore and reinstall to stable tag
paa checkout package-auto-assembler

# Prune dev checkpoints (version=0.0.0)
paa checkpoint-prune package-auto-assembler

# Preview prune
paa checkpoint-prune package-auto-assembler --dry-run
```

## Guardrails

- Prefer `--dry-run` before destructive sync actions.
- Do not assume stable tags exist; handle `dev-latest` explicitly.
- Explain that packaged history may omit `0.0.0` checkpoints by design.
- For install-related restore, verify user wants environment changes.
