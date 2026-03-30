# Import Mapping

## About

Import mapping translates Python import names into install requirement names during automatic dependency extraction.

Typical mismatch examples:
- `yaml` -> `pyyaml`
- `PIL` -> `Pillow`
- `sklearn` -> `scikit-learn`

Without this translation, extracted requirements can contain invalid or incomplete package names.

## Mapping Sources

PAA builds effective mapping from two sources:

1. bundled base mapping from installed PAA package
2. user mapping overrides from `.paa/package_mapping.json`

If the same key exists in both, user mapping wins.

## Where It Is Applied

Mapping is applied while extracting requirements from:
- main module
- CLI module (if present)
- FastAPI routes module (if present)
- Streamlit module (if present)
- MCP module (if present)

The mapping key is the import root (`module.split('.')[0]`).

## File Format

Use JSON dictionary: import name -> install name.

```json
{
  "yaml": "pyyaml",
  "PIL": "Pillow",
  "sklearn": "scikit-learn"
}
```

## If Mapping Is Not Enough

For edge cases, you can bypass mapping through source markers:

- ignore auto-detected import:
  - `import some_dep #-`
- add explicit requirement manually:
  - `#@ some-install-name`
- add optional requirement manually:
  - `#! import some_optional_dep`

This is useful when import semantics are unusual or when one import maps to multiple install-time choices.

## Operational Commands

Default mapping path:

```bash
paa test-install your-package-1
```

Override mapping file:

```bash
paa test-install your-package-1 --mapping-filepath ./.paa/package_mapping.json
paa make-package your-package-1 --mapping-filepath ./.paa/package_mapping.json
```

Inspect extracted result:

```bash
paa show-module-requirements your-package-1
```

## Related Docs

- Dependency extraction flow: `concepts/dependency_management.md`
- Config reference: `components/paa_config.md`
