# Checkpoint History

## Goal

Checkpoint history lets PAA-created packages preserve restorable package states without requiring access to the original packaging repository.

It complements package versioning by enabling local restore flows (`checkout`) across dev and stable checkpoints.

## Current Storage Model

Local history (authoring/unfolded workspace):

```text
.paa/history/<package_name>/git
```

Packaged history payload (inside installed package):

```text
.paa.tracking/git       # history work tree
.paa.tracking/git_repo  # git metadata
```

When unfolding a package, packaged history is restored back into:

```text
.paa/history/<package_name>/git
```

## Checkpoint Creation

Checkpoint creation entry points:

- Manual:
  - `paa checkpoint-create <package>`
- Test-install flow (optional):
  - `paa test-install <package> --checkpoint`
- Make-package flow (default):
  - `paa make-package <package>`
  - Use `--no-checkpoint` to skip

Checkpoint message format includes:

- `source_event` (`manual`, `test-install`, `make-package`, etc.)
- `version=<x.y.z>`
- timestamp

Tag behavior:

- `version=0.0.0` updates `dev-latest` tag
- stable versions create/use `vX.Y.Z` tags

## Listing and Inspecting History

- `paa checkpoint-list <package>`
- `paa checkpoint-show <package> <target>`

Where `<target>` can be:

- tag (for example `v1.0.0`, `dev-latest`)
- commit hash
- `latest` (for `checkpoint-show`)

## Checkout Semantics

Command:

- `paa checkout <package> [target]`

Default target resolution:

- if `target` is omitted, checkout resolves latest stable tag (`vX.Y.Z`)
- if no stable tags exist, specify explicit target (`dev-latest` or commit hash)

Flags:

- `--dry-run`: print planned changes only
- `--unfold`: apply checkpoint state to unfolded package files in current workspace
- `--no-install`: skip reinstall step

Behavior summary:

- default checkout uses a temporary workspace and runs `test-install` from that state
- `--unfold --no-install` is the “code-only restore” path

Output counters:

- `written`: new files created in package scope
- `updated`: existing files overwritten to match target
- `deleted`: package-scoped files removed because absent in target

## History Pruning

Command:

- `paa checkpoint-prune <package> [--dry-run] [--version X.Y.Z] [--commit <sha_prefix>]`

Default behavior (no selector):

- prune checkpoints with `version=0.0.0`

Selector behavior:

- `--version X.Y.Z`: prune checkpoints for that version
- `--commit <sha_prefix>`: prune specific checkpoint commit

Notes:

- pruning command modifies local history
- `--dry-run` shows effect without changes

## Packaging-Time History Sanitization

During `make-package`, PAA exports a pruned checkpoint history into packaged artifacts.

Default packaging-time prune rule:

- exclude `0.0.0` checkpoints from packaged history payload

This keeps packaged history focused on stable states while preserving full local dev history unless explicitly pruned.

## Typical Workflows

Create and inspect:

```bash
paa checkpoint-create package-auto-assembler
paa checkpoint-list package-auto-assembler
paa checkpoint-show package-auto-assembler dev-latest
```

Restore dev state to unfolded files only:

```bash
paa checkout package-auto-assembler dev-latest --dry-run --unfold --no-install
paa checkout package-auto-assembler dev-latest --unfold --no-install
```

Restore stable state and reinstall:

```bash
paa checkout package-auto-assembler
```

Prune dev checkpoints:

```bash
paa checkpoint-prune package-auto-assembler --dry-run
paa checkpoint-prune package-auto-assembler
```

## Operational Notes

- If no changes are detected during checkpoint creation, no new checkpoint commit is created.
- `dev-latest` represents mutable dev state (`0.0.0`) and moves forward when a new dev checkpoint is created.
- Stable tags (`vX.Y.Z`) remain available for deterministic checkout of released states.
