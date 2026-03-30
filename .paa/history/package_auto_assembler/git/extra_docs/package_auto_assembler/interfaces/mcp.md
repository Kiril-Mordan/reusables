# MCP Interface

## About

PAA packages can include MCP servers and run them as hosted endpoints.
This makes packaged tooling available to agent clients locally or over network.
Core dependency used under the hood: [FastMCP / MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).
For cross-component preflight checks before packaging, see `concepts/prepackaging_todo.md`.

## Quick Start

### 1. Initialize MCP scaffold for a package

```bash
paa init-mcp your-package-1
```

This creates/updates MCP source under PPR `mcp/`.

### 2. Build and install package locally

```bash
paa test-install your-package-1 --skip-deps-install
```

### 3. Register package MCP for agent (stdio mode)

```bash
paa add-mcp your-package-1
```

This registers the installed package MCP module for process/stdio client mode.
Use this mode when your agent client starts MCP via local process.
If auto-detection fails, pass `--target` and `--python-path`.

Flag guidance:
- `--target` is optional when only one supported target is auto-detected.
- `--python-path` is optional if default `python` resolves to the intended interpreter.
- `--server-name` is optional; default server name is based on package name.

### 4. Run hosted MCP from installed package

```bash
paa run-mcp --package your-package-1
```

Default MCP endpoint for streamable HTTP transport:

`http://127.0.0.1:8000/mcp`

Use this mode when your client connects to MCP over URL (hosted endpoint).

Flag guidance:
- if `.paa.mcp.config` is present, `run-mcp` can run without source/run flags.
- `--host` / `--port` are optional unless you need non-default bind settings.
- `--transport` controls hosted protocol:
  - `streamable-http` (default): endpoint on `/mcp`
  - `sse`: SSE endpoint (typically `/sse`)
- `--mode` is optional (`split` is default).
- in split mode, `--server-prefix` is optional and used only when you want prefixed server names.

### 5. Register hosted endpoint in Codex

```bash
codex mcp add paa-http --url http://127.0.0.1:8000/mcp
```

## Operational Commands

Initialize package MCP scaffold:

```bash
paa init-mcp your-package-1
```

Register installed package MCP for agent (stdio mode):

```bash
paa add-mcp your-package-1
```

List MCP tools exported by an installed package:

```bash
paa show-module-mcp your-package-1
```

Run hosted MCP endpoint:

```bash
paa run-mcp --package your-package-1 --transport streamable-http --host 127.0.0.1 --port 8000
```

Extract MCP module source from installed package:

```bash
paa extract-mcp your-package-1 --output-dir ./mcp_out
```

## Two Integration Modes

- `paa add-mcp`: process/stdio registration for agent clients.
- `paa run-mcp`: hosted network endpoint (local or remote).

Choose one mode per client integration path; most setups need only one.
Both modes can coexist if you intentionally support both client types.

## Local and Network Usage

For local machine:

```bash
paa run-mcp --package your-package-1 --host 127.0.0.1 --port 8000
```

For LAN usage:

```bash
paa run-mcp --package your-package-1 --host 0.0.0.0 --port 8000
```

Then register with host IP from another machine:

```bash
codex mcp add paa-http --url http://<host-ip>:8000/mcp
```

## Multi-Source Hosting

`run-mcp` supports multiple sources from packages and direct paths.

### Split mode (default)

Runs one hosted server per source.

```bash
paa run-mcp \
  --package your-package-1 \
  --package your-package-2 \
  --mode split \
  --host 127.0.0.1 \
  --port 8000
```

In split mode:
- default naming has no prefix (`your_package_1`, `your_package_2`)
- if `--server-prefix` (or config `RUN.server_prefix`) is provided, names become `<prefix>-<source>`

Ports are assigned incrementally starting from base `--port`.

### Combine mode

Runs one hosted server and merges tools from all sources.

```bash
paa run-mcp \
  --package your-package-1 \
  --package your-package-2 \
  --mode combine \
  --server-prefix paa-http
```

In combine mode, server name defaults to `paa-http` unless overridden.

## Optional MCP Config

`run-mcp` can load defaults from `.paa.mcp.config`.

```yaml
RUN:
  host: "0.0.0.0"
  port: 8000
  transport: "streamable-http"
  mount_path: null
  mode: "split"
  server_prefix: null

SOURCES:
  packages:
    - your-package-1
    - your-package-2
  paths: []
```

Precedence:
1. CLI flags
2. `.paa.mcp.config`
3. command defaults

## Python File Layout

### MCP module file

- path: `mcp/<module_name>.py` (or configured `mcp_dir`)
- expected structure:
  - package imports
  - `mcp = FastMCP("<server-name>")`
  - tool functions decorated with `@mcp.tool()`
  - executable block (`if __name__ == "__main__": mcp.run()`)

Recommended scaffold layout:

```python
from mcp.server.fastmcp import FastMCP
from your_package_1 import *

mcp = FastMCP("your-package-1-mcp")

@mcp.tool()
def ping(name: str = "world") -> str:
    return f"pong: hello {name}"

@mcp.tool()
def package_name() -> str:
    return "your_package_1"

if __name__ == "__main__":
    mcp.run()
```

What to edit:
- add tool functions under `@mcp.tool()` with stable names and clear docstrings.
- keep package imports at top; default import pattern is `from <package> import *`.
- keep `mcp` object name as `mcp` so PAA tooling can discover it.
- keep the executable block for direct runs.

## Notes

- Browser requests to `/` or `/docs` are expected to return `404`.
- `406 Not Acceptable` may appear for manual GET requests to `/mcp` without MCP client headers.
- For Codex/Claude process integration, use `paa add-mcp` (stdio mode registration).
