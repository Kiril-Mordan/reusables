---
name: paa-skill-management
description: "Manage PAA-packaged skills lifecycle: discover where skills live, extract single/all skills from installed PAA packages, and safely clean PAA-managed agent skills."
---

# PAA Skill Management

Use this skill when users ask to install/extract/use/remove skills shipped by PAA-created packages.

## What This Skill Covers

- Where packaged skills are expected to live.
- How skills behave in package, unfold, remove, and rename flows.
- How to extract one or all skills from installed packages.
- How to safely clean PAA-managed installed skills.

## Skill Locations

Expected repository/unfold location:

- `skills/<package_name>/<skill_name>/SKILL.md`

Packaged behavior for PAA-built packages:

- Skills can be included in package tracking as `.paa.tracking/skills`.
- `paa unfold-package <package>` restores them to `skills/<package_name>/`.
- `paa remove-package <package>` removes `skills/<package_name>/`.
- `paa rename-package <old> <new>` renames `skills/<old>/` to `skills/<new>/`.

## Commands

- `paa extract-skill <package_name> <skill_name> [--target codex|claude] [--output-dir ...]`
- `paa extract-skills <package_name> [--target codex|claude] [--output-dir ...]`
- `paa cleanup-agent-skills [--target codex|claude] [--output-dir ...]`

## Target Resolution Rules

If `--output-dir` is omitted, PAA attempts auto-detection using repository markers:

- Codex markers: `.agents`, `AGENTS.md`
- Claude markers: `.claude`, `CLAUDE.md`

If ambiguous or missing, provide `--target` or `--output-dir`.

## Safe Cleanup Behavior

Extracted skills include marker file:

- `.paa_skill_meta.yml`

`cleanup-agent-skills` removes only skill folders marked as PAA-managed (`managed_by: paa`), avoiding unmanaged/manual skills.

## Agent Procedure for “Use Skill From Package X”

1. Normalize package name (`-` and `_` form as needed).
2. Determine whether user asked for one skill or all skills.
3. Run:
   - single: `paa extract-skill ...`
   - bulk: `paa extract-skills ...`
4. If target detection fails/ambiguous, rerun with `--target` or `--output-dir`.
5. Confirm extracted destination path.
6. Continue task with the extracted skill(s).

## Guardrails

- Prefer extraction over manual copying.
- Do not delete unmanaged skills during cleanup.
- If package has no skills, report clearly and suggest checking package installation/version.
