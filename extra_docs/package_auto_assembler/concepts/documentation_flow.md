# Documentation Flow (Low-Duplication Approach)

## Goal

PAA documentation flow is designed to minimize repeated writing across README, docs site, and release notes.
The idea is to write each type of information once, in the place where it is naturally produced.

## Documentation Surfaces

PAA builds package documentation from three complementary outputs:

- `README` (package-level description and usage entry point)
- `MkDocs` site (structured, multi-page docs from extra docs + generated pages)
- `release_notes.md` (change log generated from commits)

These outputs should be consistent, but not duplicated line-by-line.

## Source-Of-Truth Pattern

Use the following source ownership model:

- Module-level docstring in `python_modules/<package>.py`:
  - canonical package summary
  - appears in README/MkDocs intro flow
- `example_notebooks/<package>.ipynb`:
  - narrative walkthrough and examples that can be converted into markdown for package docs
- `extra_docs/<package>/...`:
  - focused deep-dive docs (`.md`/`.ipynb`) organized by topic
- Commit messages:
  - release-note input, instead of manually maintaining per-release change bullets

## Release Notes From Commits

Release notes are intentionally tied to commit discipline.
Use package-scoped commit tags and optional version tags:

- `[package_name]` target package
- `[package_name][..+]` patch bump
- `[package_name][.+.]` minor bump
- `[package_name][+..]` major bump
- `[package_name][1.2.3]` explicit version

Use `;` to split one commit into multiple release-note bullets.

Example style:

`[my_package][.+.] add dependency check command; document compatibility behavior`

## Practical Split: What To Put Where

- Put stable package identity and intent in module docstring.
- Put “how to use” walkthroughs in notebook and/or focused extra docs.
- Put operational command references in CLI/interface docs.
- Put change history in commits, then let PAA generate release notes.

This keeps docs maintainable while still giving both quick and detailed entry points.

## Operational Flow

Typical local cycle:

1. Update module docstring / notebook / extra docs.
2. Run `paa test-install <package> --build-mkdocs` to refresh package outputs.
3. Validate generated README + docs site.
4. Commit with proper package/version tags and meaningful `;`-separated notes.

For release pipeline flow, see `components/repositories.md`.

## Common Pitfalls

- Rewriting the same long explanation in README and multiple extra docs pages.
- Using unstructured commit messages, then expecting useful release notes.
- Treating notebook output as final source instead of maintaining a clear source-of-truth split.
- Mixing package-level summary and deep implementation detail in one place.

## Related Docs

- Repository/commit conventions: `components/repositories.md`
- MkDocs behavior: `interfaces/mkdocs.md`
- PPR usage context: `concepts/python_packaging_repo.md`
