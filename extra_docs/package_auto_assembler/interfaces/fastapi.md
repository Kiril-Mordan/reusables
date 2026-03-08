# FastAPI Interface

## About

PAA can package and run FastAPI routes from installed packages and local route files.
Core dependency used under the hood: [FastAPI](https://fastapi.tiangolo.com/).
For package routes, PAA expects one routes file per package, with filename matching the package/module name.
For cross-component preflight checks before packaging, see `concepts/prepackaging_todo.md`.

## Quick Start

### 1. Initialize API config scaffold

```bash
paa init-api-config
```

This creates `.paa.api.config` with default `DESCRIPTION`, `MIDDLEWARE`, and `RUN`.

### 1a. Initialize API routes scaffold for a package

```bash
paa init-api your-package-1
```

This creates `api_routes/your_package_1.py` (or configured `api_routes_dir`).

### 2. Run API using packaged routes

```bash
paa run-api-routes --package your-package-1
```

### 3. Add multiple package route sources

```bash
paa run-api-routes --package your-package-1 --package your-package-2
```

### 4. Add local route file(s)

```bash
paa run-api-routes --route ./api_routes/your_package_1.py
```

### 5. Include static docs paths

```bash
paa run-api-routes --docs ./your-package-1_temp_mkdocs/site
```

## Operational Commands

Initialize API config:

```bash
paa init-api-config
```

Initialize package route scaffold:

```bash
paa init-api your-package-1
```

Run API from packaged routes:

```bash
paa run-api-routes --package your-package-1
```

Run API from local route file:

```bash
paa run-api-routes --route ./api_routes/your_package_1.py
```

Run API with additional static docs mount:

```bash
paa run-api-routes --package your-package-1 --docs ./your-package-1_temp_mkdocs/site
```

## Optional `.paa.api.config`

```yaml
DESCRIPTION:
  title: "PAA API"
  description: "API routes served by package-auto-assembler."
  version: "0.0.0"

MIDDLEWARE:
  allow_origins: ["*"]
  allow_credentials: true
  allow_methods: ["*"]
  allow_headers: ["*"]

RUN:
  host: "0.0.0.0"
  port: 8000
```

Precedence:
1. CLI flags (`--host`, `--port`)
2. `.paa.api.config`
3. command defaults

## File Layout

### API config file

- path: `.paa.api.config`
- sections:
  - `DESCRIPTION`: FastAPI app metadata (`title`, `description`, `version`)
  - `MIDDLEWARE`: CORS middleware parameters
  - `RUN`: uvicorn run settings (`host`, `port`, ...)

What to edit:
- update `DESCRIPTION` to reflect your API title/version text
- tighten `MIDDLEWARE.allow_origins` for non-local deployments
- set `RUN.host` and `RUN.port` for your target environment

### API routes module

- path: `api_routes/<module_name>.py` (or custom `api_routes_dir`)
- must expose `router = APIRouter(...)`
- include route handlers decorated with `@router.get(...)`, `@router.post(...)`, etc.
- default scaffold from `init-api` uses a package prefix:
  - `router = APIRouter(prefix="/<package-name>")`

Recommended generated layout:

```python
from fastapi import APIRouter
from your_package_1.your_package_1 import *

router = APIRouter(prefix="/your-package-1")

@router.get("/health")
def health():
    return {"status": "ok", "package": "your-package-1"}

@router.get("/version")
def package_version():
    return {"version": "0.0.0"}
```

With this layout, endpoints are:
- `/your-package-1/health`
- `/your-package-1/version`

## Importing From Packages

Recommended pattern in route modules:

```python
from fastapi import APIRouter
from your_package_1.your_package_1 import *

router = APIRouter(prefix="/your-package-1")

@router.get("/version")
def package_version():
    return {"version": "0.0.0"}
```

Guidance:
- prefer importing from packaged module implementation path
  (`from <package_name>.<package_name> import ...`) as used by existing API route modules.
- avoid importing PPR component files directly in route modules.
- keep heavy initialization outside import-time where possible.

## Flag Guidance

- `--api-config` is optional; default is `.paa.api.config`.
- `--host` / `--port` are optional unless you need non-default bind settings.
- `--package`, `--route`, and `--docs` are repeatable and can be mixed.

## Local and Network Usage

Local:

```bash
paa run-api-routes --package your-package-1 --host 127.0.0.1 --port 8000
```

LAN:

```bash
paa run-api-routes --package your-package-1 --host 0.0.0.0 --port 8000
```

## Notes

- Routes from installed packages are loaded from their packaged `routes.py`.
- If packaged docs site exists, package docs are mounted under package-specific docs path.
- Additional docs paths passed via `--docs` are mounted under `/mkdocs`, `/mkdocs1`, `/mkdocs2`, etc.
- FastAPI framework docs are global and not package-prefixed:
  - Swagger UI: `/docs`
  - OpenAPI JSON: `/openapi.json`
- Imports from package route files are included in dependency extraction during packaging, similar to the main module.
