import logging
import os
import ast
import re
import attrs
import attrsx

@attrsx.define
class LocalDependaciesHandler:

    """
    Contains set of tools to extract and combine package dependencies.

    Usage example:
    ```python
    ldh = LocalDependaciesHandler(
        main_module_filepath="python_modules/your_package.py",
        dependencies_dir="python_modules/components",
        save_filepath="your_package_temp/your_package.py",
    )
    ldh.combine_modules()
    ```
    """

    main_module_filepath = attrs.field()
    dependencies_dir = attrs.field()
    save_filepath = attrs.field(default="./combined_module.py")
    add_empty_design_choices = attrs.field(default=False, type = bool)

    # output
    filtered_dep_names_list = attrs.field(default=[])
    dependencies_names_list = attrs.field(init=False)
    combined_module = attrs.field(init=False)

    logger = attrs.field(default=None)
    logger_name = attrs.field(default='Local Dependacies Handler')
    loggerLvl = attrs.field(default=logging.INFO)
    logger_format = attrs.field(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _read_module(self,
                    filepath : str) -> str:

        """
        Method for reading in module.
        """

        with open(filepath, 'r') as file:
            return file.read()

    def _extract_module_docstring(self,
                                 module_content : str) -> str:

        """
        Method for extracting title, module level docstring.
        """

        match = re.match(r'(""".*?"""|\'\'\'.*?\'\'\')', module_content, re.DOTALL)
        return match.group(0) if match else ''

    def _extract_imports(self,
                        module_content : str) -> str:

        """
        Method for extracting import statements from the module.
        """

        try:
            parsed_tree = ast.parse(module_content)
        except SyntaxError:
            # Fallback to previous behavior if parsing fails.
            return re.findall(r'^(?:from\s+.+\s+)?import\s+.+$', module_content, re.MULTILINE)

        lines = module_content.splitlines()
        imports = []

        # Keep only module-level imports. Do not hoist function-local imports.
        import_nodes = [
            node for node in parsed_tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        import_nodes = sorted(import_nodes, key=lambda node: (node.lineno, getattr(node, "end_lineno", node.lineno)))

        for node in import_nodes:
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            import_block = "\n".join(lines[start:end]).strip()
            if import_block:
                imports.append(import_block)

        return imports

    def _remove_module_docstring(self,
                                module_content : str) -> str:

        """
        Method for removing title, module level docstring.
        """

        return re.sub(r'^(""".*?"""|\'\'\'.*?\'\'\')', '', module_content, flags=re.DOTALL).strip()

    def _remove_imports(self,
                       module_content : str) -> str:

        """
        Method for removing import statements from the module.
        """

        try:
            parsed_tree = ast.parse(module_content)
        except SyntaxError:
            module_content = re.sub(r'^(?:from\s+.+\s+)?import\s+.+$', '', module_content, flags=re.MULTILINE)
            return module_content.strip()

        lines = module_content.splitlines()
        line_mask = [True] * len(lines)

        # Remove only module-level imports. Keep function-local imports in place.
        import_nodes = [
            node for node in parsed_tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]

        for node in import_nodes:
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            for line_idx in range(start, min(end, len(line_mask))):
                line_mask[line_idx] = False

        filtered_lines = [line for keep, line in zip(line_mask, lines) if keep]
        return "\n".join(filtered_lines).strip()

    def _remove_metadata(self, module_content: str) -> str:
        """
        Method for removing metadata from the module, including __package_metadata__ and __design_choices__.
        """

        lines = module_content.split('\n')
        new_lines = []
        inside_metadata = False

        for line in lines:
            if line.strip().startswith("__package_metadata__ = {") or line.strip().startswith("__design_choices__ = {"):
                inside_metadata = True
            elif inside_metadata and '}' in line:
                inside_metadata = False
                continue  # Skip adding this line to new_lines

            if not inside_metadata:
                new_lines.append(line)

        return '\n'.join(new_lines)

    def _extract_design_choices(self,
                                module_content: str,
                                module_name: str,
                                return_empty : bool = False) -> dict:

        """
        Extract __design_choices__ dictionary from the module.
        """

        design_choices_pattern = r'^__design_choices__\s*=\s*({.*?})\s*(?:\n|$)'
        match = re.search(design_choices_pattern, module_content, re.DOTALL)
        if match:
            try:
                design_choices = ast.literal_eval(match.group(1))
                return {module_name: design_choices}
            except Exception as e:
                self.logger.error(f"Error evaluating __design_choices__ in {module_name}: {e}")
        if return_empty:
            return {module_name: {}}

        return None

    def _combine_design_choices(self, design_choices_list: list) -> dict:

        """
        Combine __design_choices__ dictionaries from all modules.
        """

        design_choices = {}
        for design_choice in design_choices_list:
            design_choices.update(design_choice)
        return design_choices

    def _get_local_dependencies_path(self, 
                                     main_module_filepath : str,
                                     dependencies_dir : str):


        # Read main module
        main_module_content = self._read_module(main_module_filepath)

        # Extract and preserve the main module's docstring and imports
        main_module_docstring = self._extract_module_docstring(main_module_content)
        main_module_content = self._remove_module_docstring(main_module_content)
        main_module_imports = self._extract_imports(main_module_content)

        # List of dependency module names
        dependencies = [os.path.splitext(f)[0] for f in os.listdir(dependencies_dir) if f.endswith('.py')]
        # List of dependency bundles
        dependencies_folders = [os.path.splitext(f)[0] for f in os.listdir(dependencies_dir) \
            if os.path.isdir(os.path.join(dependencies_dir,f))]
        # List of dependencies from bundles
        bundle_dependencies = [os.path.splitext(f)[0] for bundle in dependencies_folders \
            for f in os.listdir(os.path.join(dependencies_dir, bundle)) if f.endswith('.py')]
        bundle_dep_path = [os.path.join(bundle, f) for bundle in dependencies_folders \
            for f in os.listdir(os.path.join(dependencies_dir, bundle)) if f.endswith('.py')]

        self.dependencies_names_list = dependencies + bundle_dependencies
        # Filtering relevant dependencies
        module_local_deps = [dep for dep in dependencies for module in main_module_imports if f'{dep} import' in module]
        module_bundle_deps = [dep for dep in bundle_dependencies for module in main_module_imports if f'{dep} import' in module]
        
        bundle_deps = [(file_path, filename) \
            for file_path, filename in zip(bundle_dep_path, bundle_dependencies) \
                if filename in module_bundle_deps]
        
        module_bundle_deps_path = [path for dep, path in zip(bundle_dependencies,bundle_dep_path) \
            for module in main_module_imports if f'{dep} import' in module]

        return (main_module_docstring,
                main_module_content,
                main_module_imports,
                module_local_deps, 
                module_bundle_deps, 
                module_bundle_deps_path, 
                bundle_deps)

    def get_module_deps_path(self,
                            main_module_filepath : str = None,
                            dependencies_dir : str = None):

        """
        Get paths to local dependencies referenced in the module.
        """

        if main_module_filepath is None:
            main_module_filepath = self.main_module_filepath

        if dependencies_dir is None:
            dependencies_dir = self.dependencies_dir

        if dependencies_dir:

            (main_module_docstring,
            main_module_content,
            main_module_imports,
            module_local_deps, 
            module_bundle_deps, 
            module_bundle_deps_path, 
            bundle_deps) = self._get_local_dependencies_path(
                main_module_filepath = main_module_filepath,
                dependencies_dir = dependencies_dir
            )

            module_local_deps = [os.path.join(dependencies_dir,p) for p in module_local_deps]
            module_bundle_deps = [os.path.join(dependencies_dir,p[0]) for p in bundle_deps]

            file_paths = [main_module_filepath] + module_local_deps + module_bundle_deps

        else:
            file_paths = [main_module_filepath]

        return file_paths

    def _validate_selected_components_have_no_component_imports(
        self,
        dependencies_dir: str,
        selected_component_paths: list
    ):
        """
        Ensure selected components do not import any local component module.
        """

        if not selected_component_paths:
            return

        component_names = set()
        for root, _, files in os.walk(dependencies_dir):
            for filename in files:
                if filename.endswith(".py"):
                    component_names.add(os.path.splitext(filename)[0])
        deps_namespace_tokens = {
            token for token in os.path.normpath(dependencies_dir).split(os.sep)
            if token and token not in {".", ".."}
        }

        def _is_local_component_path_import(import_path: str) -> bool:
            """
            Detect imports that point back to local components through a dotted path.
            Uses runtime dependencies_dir tokens (effective config/default path), not hardcoded names.
            """

            if not import_path:
                return False
            segments = [seg for seg in import_path.split(".") if seg]
            if not segments:
                return False
            has_component_segment = any(seg in component_names for seg in segments)
            has_deps_namespace_segment = any(seg in deps_namespace_tokens for seg in segments)
            return has_component_segment and has_deps_namespace_segment

        violations = []
        for rel_path in selected_component_paths:
            abs_path = os.path.join(dependencies_dir, rel_path)
            try:
                with open(abs_path, "r", encoding="utf-8") as file:
                    parsed = ast.parse(file.read())
            except (FileNotFoundError, SyntaxError):
                continue

            for node in ast.walk(parsed):
                if isinstance(node, ast.ImportFrom):
                    module_name = node.module or ""
                    if node.level and node.level > 0:
                        violations.append((rel_path, f"from {'.' * node.level}{module_name} import ..."))
                        continue

                    root_name = module_name.split(".")[0] if module_name else ""
                    if (
                        root_name == "components"
                        or root_name in component_names
                        or ".components." in module_name
                        or _is_local_component_path_import(module_name)
                    ):
                        violations.append((rel_path, f"from {module_name} import ..."))

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        import_name = alias.name
                        root_name = import_name.split(".")[0]
                        if (
                            root_name == "components"
                            or root_name in component_names
                            or ".components." in import_name
                            or _is_local_component_path_import(import_name)
                        ):
                            violations.append((rel_path, f"import {import_name}"))

        if violations:
            details = "; ".join([f"{path}: {stmt}" for path, stmt in violations])
            raise ValueError(
                "Selected components must not import local components directly. "
                "Wire dependency flow through the main module. "
                f"Violations: {details}"
            )


    def combine_modules(self,
                        main_module_filepath : str = None,
                        dependencies_dir : str = None,
                        add_empty_design_choices : bool = None) -> str:

        """
        Combining main module with its local dependancies.
        """

        if main_module_filepath is None:
            main_module_filepath = self.main_module_filepath

        if dependencies_dir is None:
            dependencies_dir = self.dependencies_dir

        if add_empty_design_choices is None:
            add_empty_design_choices = self.add_empty_design_choices


        (main_module_docstring,
        main_module_content,
        main_module_imports,
        module_local_deps, 
        module_bundle_deps, 
        module_bundle_deps_path, 
        bundle_deps) = self._get_local_dependencies_path(
            main_module_filepath = main_module_filepath,
            dependencies_dir = dependencies_dir
        )

        # Remove specific dependency imports from the main module
        for dep in module_local_deps:
            main_module_imports0 = main_module_imports
            main_module_imports = [imp for imp in main_module_imports if f'{dep} import' not in imp]
            if main_module_imports != main_module_imports0:
                self.filtered_dep_names_list.append(f"{dep}.py")

        for dep,dep_path in zip(module_bundle_deps,module_bundle_deps_path):
            main_module_imports0 = main_module_imports
            main_module_imports = [imp for imp in main_module_imports if f'{dep} import' not in imp]
            if main_module_imports != main_module_imports0:
                self.filtered_dep_names_list.append(dep_path)

        selected_component_paths = [f"{dep}.py" for dep in module_local_deps] + [path for path, _ in bundle_deps]
        self._validate_selected_components_have_no_component_imports(
            dependencies_dir=dependencies_dir,
            selected_component_paths=selected_component_paths
        )

        main_module_content = self._remove_imports(main_module_content)

        # Process dependency modules
        combined_content = ""
        design_choices_list = []

        for filename in module_local_deps:

            dep_content = self._read_module(os.path.join(dependencies_dir, f"{filename}.py"))
            # Extract design choices and add to list
            design_choices = self._extract_design_choices(dep_content, filename,add_empty_design_choices)
            if design_choices:
                design_choices_list.append(design_choices)

            dep_content = self._remove_module_docstring(dep_content)
            dep_content = self._remove_metadata(dep_content)
            dep_imports = self._extract_imports(dep_content)
            main_module_imports.extend(dep_imports)
            combined_content += self._remove_module_docstring(self._remove_imports(dep_content)) + "\n\n"

        
        # Process bundle dependency modules
        for file_path, filename in bundle_deps:

            dep_content = self._read_module(os.path.join(dependencies_dir, file_path))
            # Extract design choices and add to list
            design_choices = self._extract_design_choices(dep_content, filename,add_empty_design_choices)
            if design_choices:
                design_choices_list.append(design_choices)

            dep_content = self._remove_module_docstring(dep_content)
            dep_content = self._remove_metadata(dep_content)
            dep_imports = self._extract_imports(dep_content)
            main_module_imports.extend(dep_imports)
            combined_content += self._remove_module_docstring(self._remove_imports(dep_content)) + "\n\n"

        # Combine design choices from all modules
        combined_design_choices = self._combine_design_choices(design_choices_list)
        combined_design_choices_str = f"__design_choices__ = {combined_design_choices}\n\n"

        # Combine everything
        unique_imports = sorted(set(main_module_imports), key=lambda x: main_module_imports.index(x))
        combined_module = main_module_docstring + "\n\n" + '\n'.join(unique_imports) + \
            "\n\n" + combined_design_choices_str + combined_content + main_module_content

        self.combined_module = combined_module

        return combined_module

    def save_combined_modules(self,
                              combined_module : str = None,
                              save_filepath : str = None):

        """
        Save combined module to .py file.
        """

        if combined_module is None:
            combined_module = self.combine_modules

        if save_filepath is None:
            save_filepath = self.save_filepath

        with open(save_filepath, 'w', encoding = "utf-8") as file:
            file.write(combined_module)
