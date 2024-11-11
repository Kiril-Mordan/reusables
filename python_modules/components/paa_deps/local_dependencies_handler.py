import logging
import os
import ast
import re
import attr #>=22.2.0

@attr.s
class LocalDependaciesHandler:

    """
    Contains set of tools to extract and combine package dependencies.
    """

    main_module_filepath = attr.ib()
    dependencies_dir = attr.ib()
    save_filepath = attr.ib(default="./combined_module.py")
    add_empty_design_choices = attr.ib(default=False, type = bool)

    # output
    filtered_dep_names_list = attr.ib(default=[])
    dependencies_names_list = attr.ib(init=False)
    combined_module = attr.ib(init=False)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Local Dependacies Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

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

        return re.findall(r'^(?:from\s+.+\s+)?import\s+.+$', module_content, re.MULTILINE)

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

        module_content = re.sub(r'^(?:from\s+.+\s+)?import\s+.+$', '', module_content, flags=re.MULTILINE)
        return module_content.strip()

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