# Skills

## Motivation

In PAA, skills are first-class package assets. Like docs, artifacts, and licenses, they can be versioned with the package lifecycle and shipped inside built packages.

Skills are also agent-friendly usage docs: concise, execution-oriented guidance for tools/agents. They can document how to use capabilities provided by the package itself, complementing user-facing docs.

## Source Structure in PPR

Skills are authored in the packaging repository under:

`skills/<package_name>/<skill_name>/SKILL.md`

Recommended layout keeps skills namespaced by package to avoid collisions between packages that provide similarly named skills.

## Packaging and Unfold Lifecycle

During packaging, skills are included in package tracking data as:

`.paa.tracking/skills`

During local package workflows:

- `paa unfold-package <package>` restores skills into `skills/<package_name>/`
- `paa remove-package <package>` removes `skills/<package_name>/`
- `paa rename-package <old> <new>` renames `skills/<old>/` to `skills/<new>/`

This keeps skills aligned with code and package identity through refactors.

## Extracting Skills for Agents

PAA provides extraction commands for installed packages:

- `paa extract-skill <package> <skill_name>`
- `paa extract-skills <package>`

Targets:

- Codex: `.agents/skills`
- Claude: `.claude/skills`

Target resolution:

- If `--output-dir` is provided, it is used directly.
- Otherwise PAA detects target roots by walking upward from current directory.
- If no markers are found, Codex extraction falls back to `~/.agents/skills`.

## Managed Cleanup

Extracted skills include a marker file:

`.paa_skill_meta.yml`

This enables safe cleanup via:

`paa cleanup-agent-skills`

Only PAA-managed extracted skills are removed, leaving unmanaged/manual skills untouched.

## Suggested Skills for This Package

Recommended skills currently maintained for `package_auto_assembler`:

- `paa-package-creation`: package structure, single-module wiring, and validation flow.
- `paa-inspect-functions`: read-only inspection of installed package metadata/assets.
- `paa-skill-management`: extraction/cleanup lifecycle for packaged skills.
- `paa-checkpoint-history`: checkpoint create/list/show/checkout/prune workflows, including safe restore patterns.
