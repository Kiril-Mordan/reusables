---
name: paa-inspect-functions
description: Inspect installed PAA packages using read-only PAA CLI inspection commands (module info, requirements, licenses, artifacts, local dependency references, and tracked version).
---

# PAA Inspect Functions

Use this skill when a user asks to inspect a package created with PAA, validate package state, or gather package diagnostics without rebuilding.

## Trigger Conditions

Use this skill for requests like:

- "inspect package info"
- "show package requirements/licenses/artifacts"
- "check tracked version"
- "show local dependency references"

Do not use this skill for packaging/build flows (`make-package`, `test-install`) unless explicitly requested.

## Primary Commands

- `paa show-module-list`
- `paa show-module-info <package>`
- `paa show-module-requirements <package>`
- `paa show-module-licenses <package>`
- `paa show-module-artifacts <package>`
- `paa show-module-artifacts-links <package>`
- `paa show-ref-local-deps <package>`
- `paa extract-tracking-version <module_name>`

## Workflow

1. Normalize package name for command context:
   - module file naming uses underscores
   - CLI inputs may use hyphens
2. Run a small first check only:
   - `paa show-module-info <package>`
3. Return the result and ask the user if they want deeper checks.
4. Only if user confirms, run additional inspections:
   - requirements
   - licenses
   - artifacts and artifact links
   - local dependency references
   - tracked version
5. If user asks for package discovery, run `show-module-list`.
6. Summarize findings by category with clear pass/fail/unknown signals.

## Output Contract

Provide results in this order:

1. Package identity and version
2. Requirements summary
3. License summary
4. Artifacts and links summary
5. Local dependency references
6. Notable issues and next checks

Keep outputs concise and command-grounded.

## Guardrails

- Prefer read-only inspection commands.
- Start with minimal scope (`show-module-info`) and ask before expanding.
- Do not run all inspection commands unless user explicitly asks for full inspection.
- Do not run build/test/install commands unless explicitly requested.
- If a command fails, report exact failure point and continue with remaining inspections when possible.
