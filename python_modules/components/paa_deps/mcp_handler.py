import os
import sys
import shutil
import importlib
import importlib.util
import multiprocessing
import re
import attrs
import attrsx
from mcp.server.fastmcp import FastMCP


def _run_mcp_source_process(mcp_filepath: str,
                            host: str,
                            port: int,
                            transport: str,
                            mount_path: str = None,
                            server_name: str = None):
    """
    Run one MCP source in a standalone process.
    """

    spec = importlib.util.spec_from_file_location(
        f"paa_runtime_mcp_{abs(hash((mcp_filepath, server_name, port)))}",
        mcp_filepath
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load MCP module spec from {mcp_filepath}")

    mcp_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mcp_module)

    mcp_app = getattr(mcp_module, "mcp", None)
    if mcp_app is None:
        raise RuntimeError(f"No FastMCP app named 'mcp' in {mcp_filepath}")

    if server_name:
        try:
            mcp_app.name = server_name
        except Exception:
            pass

    if hasattr(mcp_app, "settings"):
        mcp_app.settings.host = host
        mcp_app.settings.port = int(port)
        if mount_path is not None:
            mcp_app.settings.mount_path = mount_path

    mcp_app.run(transport=transport, mount_path=mount_path)


@attrsx.define
class McpHandler:

    """
    Contains tools to prepare and handle MCP server code for packages.
    """

    # inputs
    mcp_filepath = attrs.field(default=None)
    setup_directory = attrs.field(default=None)
    package_name = attrs.field(default=None)

    def prepare_mcp(self,
                    mcp_filepath: str = None,
                    setup_directory: str = None):

        """
        Prepare MCP module for packaging.
        """

        if mcp_filepath is None:
            mcp_filepath = self.mcp_filepath

        if setup_directory is None:
            setup_directory = self.setup_directory

        if mcp_filepath is None:
            raise ImportError("Parameter mcp_filepath is missing!")

        if setup_directory is None:
            raise ImportError("Parameter setup_directory is missing!")

        shutil.copy(mcp_filepath, os.path.join(setup_directory, "mcp_server.py"))
        return True

    def run_app(self,
                package_name: str = None,
                mcp_filepath: str = None,
                host: str = "127.0.0.1",
                port: int = 8000,
                transport: str = "streamable-http",
                mount_path: str = None):

        """
        Runs hosted MCP server from a package or provided filepath.
        """

        if mcp_filepath is None:
            mcp_filepath = self.mcp_filepath

        if package_name is None:
            package_name = self.package_name

        if package_name:
            try:
                package_name = package_name.replace("-", "_")
                package = importlib.import_module(package_name)
                package_dir = os.path.dirname(package.__file__)
                mcp_filepath = os.path.join(package_dir, "mcp_server.py")
            except ImportError as e:
                self.logger.error(f"Error importing mcp from {package_name}: {e}")
                sys.exit(1)

        if not mcp_filepath or (not os.path.exists(mcp_filepath)):
            raise ValueError(f"Provide valid mcp filepath, {mcp_filepath} not found!")

        spec = importlib.util.spec_from_file_location("paa_runtime_mcp", mcp_filepath)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load MCP module spec from {mcp_filepath}")

        mcp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcp_module)

        mcp_app = getattr(mcp_module, "mcp", None)
        if mcp_app is None:
            raise RuntimeError(f"No FastMCP app named 'mcp' in {mcp_filepath}")

        if hasattr(mcp_app, "settings"):
            mcp_app.settings.host = host
            mcp_app.settings.port = int(port)
            if mount_path is not None:
                mcp_app.settings.mount_path = mount_path

        self.logger.info(
            f"Starting MCP server transport={transport} host={host} port={port} "
            f"from {mcp_filepath}"
        )
        mcp_app.run(transport=transport, mount_path=mount_path)

    def _source_id_from_package(self,
                                package_name: str):
        return package_name.replace("-", "_")

    def _source_id_from_path(self,
                             filepath: str):
        stem = os.path.splitext(os.path.basename(filepath))[0]
        cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", stem).strip("_")
        return cleaned or "mcp_source"

    def _resolve_source(self,
                        package_name: str = None,
                        mcp_filepath: str = None):

        if package_name:
            package_name = package_name.replace("-", "_")
            try:
                package = importlib.import_module(package_name)
                package_dir = os.path.dirname(package.__file__)
                mcp_filepath = os.path.join(package_dir, "mcp_server.py")
            except ImportError as e:
                self.logger.error(f"Error importing mcp from {package_name}: {e}")
                raise
            source_id = self._source_id_from_package(package_name)
        else:
            source_id = self._source_id_from_path(mcp_filepath)

        if not mcp_filepath or (not os.path.exists(mcp_filepath)):
            raise ValueError(f"Provide valid mcp filepath, {mcp_filepath} not found!")

        return source_id, os.path.abspath(mcp_filepath)

    def _load_mcp_app(self,
                      mcp_filepath: str,
                      source_id: str):
        spec = importlib.util.spec_from_file_location(
            f"paa_runtime_mcp_{source_id}",
            mcp_filepath
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load MCP module spec from {mcp_filepath}")

        mcp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcp_module)
        mcp_app = getattr(mcp_module, "mcp", None)
        if mcp_app is None:
            raise RuntimeError(f"No FastMCP app named 'mcp' in {mcp_filepath}")
        return mcp_app

    def _resolve_sources(self,
                         package_names: list = None,
                         mcp_filepaths: list = None):

        package_names = [p for p in (package_names or []) if p]
        mcp_filepaths = [p for p in (mcp_filepaths or []) if p]

        sources = []
        used_ids = {}

        for package_name in package_names:
            source_id, filepath = self._resolve_source(package_name=package_name)
            source_id_base = source_id
            suffix = 2
            while source_id in used_ids:
                source_id = f"{source_id_base}_{suffix}"
                suffix += 1
            used_ids[source_id] = filepath
            sources.append((source_id, filepath))

        for mcp_filepath in mcp_filepaths:
            source_id, filepath = self._resolve_source(mcp_filepath=mcp_filepath)
            source_id_base = source_id
            suffix = 2
            while source_id in used_ids:
                source_id = f"{source_id_base}_{suffix}"
                suffix += 1
            used_ids[source_id] = filepath
            sources.append((source_id, filepath))

        if not sources:
            raise ValueError("At least one MCP source is required.")

        return sources

    def _set_app_runtime(self,
                         mcp_app,
                         server_name: str,
                         host: str,
                         port: int,
                         mount_path: str = None):
        try:
            mcp_app.name = server_name
        except Exception:
            pass

        if hasattr(mcp_app, "settings"):
            mcp_app.settings.host = host
            mcp_app.settings.port = int(port)
            if mount_path is not None:
                mcp_app.settings.mount_path = mount_path

    def _copy_tool(self,
                   host_app,
                   source_tool,
                   target_name: str):
        host_app._tool_manager.add_tool(
            source_tool.fn,
            name=target_name,
            title=getattr(source_tool, "title", None),
            description=getattr(source_tool, "description", None),
            annotations=getattr(source_tool, "annotations", None),
            icons=getattr(source_tool, "icons", None),
            meta=getattr(source_tool, "meta", None),
        )

    def _run_combine_mode(self,
                          sources: list,
                          host: str,
                          port: int,
                          transport: str,
                          mount_path: str = None,
                          server_prefix: str = None):
        server_name = server_prefix if server_prefix else "paa-http"

        host_app = FastMCP(server_name, host=host, port=int(port))

        source_tools = []
        name_counts = {}
        for source_id, source_path in sources:
            source_app = self._load_mcp_app(
                mcp_filepath=source_path,
                source_id=source_id
            )
            tools = source_app._tool_manager.list_tools()
            for tool in tools:
                tool_name = getattr(tool, "name", None)
                if tool_name is None:
                    continue
                name_counts[tool_name] = name_counts.get(tool_name, 0) + 1
                source_tools.append((source_id, tool))

        for source_id, tool in source_tools:
            original_name = tool.name
            if name_counts.get(original_name, 0) > 1:
                target_name = f"{source_id}__{original_name}"
            else:
                target_name = original_name
            self._copy_tool(
                host_app=host_app,
                source_tool=tool,
                target_name=target_name
            )

        self.logger.info(
            "Starting combined MCP server "
            f"name={server_name} transport={transport} host={host} port={port} "
            f"sources={[source_id for source_id, _ in sources]}"
        )
        host_app.run(transport=transport, mount_path=mount_path)

    def _run_split_mode(self,
                        sources: list,
                        host: str,
                        port: int,
                        transport: str,
                        mount_path: str = None,
                        server_prefix: str = None):
        if len(sources) == 1:
            source_id, source_path = sources[0]
            server_name = f"{server_prefix}-{source_id}" if server_prefix else source_id
            self.logger.info(
                "Starting split MCP server "
                f"name={server_name} transport={transport} host={host} port={port} "
                f"source={source_id}"
            )
            _run_mcp_source_process(
                mcp_filepath=source_path,
                host=host,
                port=int(port),
                transport=transport,
                mount_path=mount_path,
                server_name=server_name
            )
            return

        processes = []
        for idx, (source_id, source_path) in enumerate(sources):
            source_port = int(port) + idx
            server_name = f"{server_prefix}-{source_id}" if server_prefix else source_id
            self.logger.info(
                "Starting split MCP server "
                f"name={server_name} transport={transport} host={host} port={source_port} "
                f"source={source_id}"
            )
            process = multiprocessing.Process(
                target=_run_mcp_source_process,
                args=(source_path, host, source_port, transport, mount_path, server_name),
                daemon=False
            )
            process.start()
            processes.append(process)

        try:
            for process in processes:
                process.join()
        except KeyboardInterrupt:
            self.logger.info("Stopping split MCP servers...")
            for process in processes:
                if process.is_alive():
                    process.terminate()
            for process in processes:
                process.join()

    def run_apps(self,
                 package_names: list = None,
                 mcp_filepaths: list = None,
                 host: str = "127.0.0.1",
                 port: int = 8000,
                 transport: str = "streamable-http",
                 mount_path: str = None,
                 mode: str = "split",
                 server_prefix: str = None):
        """
        Run hosted MCP in split or combine mode from selected sources.
        """

        mode = (mode or "split").lower()
        if mode not in {"split", "combine"}:
            raise ValueError("mode must be one of: split, combine")

        sources = self._resolve_sources(
            package_names=package_names,
            mcp_filepaths=mcp_filepaths
        )

        if mode == "combine":
            self._run_combine_mode(
                sources=sources,
                host=host,
                port=int(port),
                transport=transport,
                mount_path=mount_path,
                server_prefix=server_prefix
            )
        else:
            self._run_split_mode(
                sources=sources,
                host=host,
                port=int(port),
                transport=transport,
                mount_path=mount_path,
                server_prefix=server_prefix
            )

    def extract_mcp_from_package(self,
                                 package_name: str,
                                 output_directory: str = None,
                                 output_filepath: str = None):

        """
        Extracts MCP server file from the specified package.
        """

        try:
            if output_directory is None:
                output_directory = "."

            package = importlib.import_module(package_name)
            package_dir = os.path.dirname(package.__file__)

            mcp_file_path = os.path.join(package_dir, "mcp_server.py")
            if not os.path.exists(mcp_file_path):
                self.logger.warning(f"No MCP server file found in package '{package_name}'.")
                return

            with open(mcp_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            content = content.replace(f"{package_name}.{package_name}", package_name)

            os.makedirs(output_directory, exist_ok=True)

            if output_filepath is None:
                output_filepath = os.path.join(output_directory, f"{package_name}_mcp_server.py")

            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Extracted MCP server from package '{package_name}' to '{output_filepath}'.")
        except ImportError:
            self.logger.error(f"Package '{package_name}' not found.")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
