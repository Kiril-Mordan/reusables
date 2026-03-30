# Artifacts Component

## About

In PAA, artifacts are package-attached files and metadata produced during packaging and later available from the installed package.
They are part of the package lifecycle, not a separate runtime interface.

This component explains artifact behavior across:
- unfolded PPR structure (editable source repo layout)
- packaged structure (installed dependency layout)

## Artifact Types

PAA packages can include:

- tracking files under `.paa/tracking`
- optional MkDocs site under `mkdocs/`
- optional user artifacts copied from `artifacts/<package_name>/`
- optional tests copied from `tests/<package_name>/`

Tracking files are tool metadata used by PAA workflows (version tracking, release notes inputs, mapping files, etc.).

## Package vs Unfold Behavior

### During package build

When `paa make-package` or `paa test-install` prepares the setup directory, PAA assembles package artifacts into installable layout.

Typical result in packaged module:
- `package_name/.paa/...` tracking data
- `package_name/mkdocs/site/...` (if docs were built)
- `package_name/artifacts/...` (if artifact files were provided)
- `package_name/tests/...` (if tests were included)

### During unfold

`paa unfold-package <package>` reconstructs editable PPR-like structure from installed package content.

Artifact-related behavior in unfold flow:
- packaged tracking content is written back into local `.paa/...` paths used by the repository
- packaged docs/artifacts/tests are restored to configured repo locations when available
- restoration follows current `.paa.config` path mapping

This is why unfolding can re-create package-associated auxiliary files even outside the original repository.

## Artifact Sources

User-provided artifacts can come from:

1. filesystem inputs in `artifacts/<package_name>/`
2. link files (`*.link`) stored in artifact directory
3. `artifact_urls` entries in package metadata (`__package_metadata__`)

For link-based inputs, PAA resolves/downloads content during packaging so final artifacts are physically bundled with the package.
For metadata field details, see `components/package_metadata.md`.

## Operational Commands

Inspect packaged artifact records (without extraction):

```bash
paa show-module-artifacts your-package-1
paa show-module-artifacts-links your-package-1
```

Refresh artifact records for a module:

```bash
paa refresh-module-artifacts your-package-1
```

Build/install with artifacts:

```bash
paa test-install your-package-1 --skip-deps-install
```

Extract packaged artifacts from installed dependency:

```bash
paa extract-module-artifacts your-package-1 --output-dir ./artifacts_out
```

Extract packaged docs site:

```bash
paa extract-module-site your-package-1 --output-dir ./site_out
```

`show-*` commands list artifact metadata/locations, `refresh-module-artifacts` updates module artifact records, and `extract-*` commands copy files to your target directory.

## Practical Notes

- Keep artifact naming stable to avoid confusion across versions.
- Prefer deterministic artifact generation for reproducible package builds.
- For docs-related images, follow mkdocs docs guidance on drawio conversion and file naming to avoid collisions.
- Treat large binary artifacts deliberately, as they increase package size and install time.
