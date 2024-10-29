import logging
import os
import re
import attr #>=22.2.0
from stdlib_list import stdlib_list
from packaging import version
import tempfile

@attr.s
class RequirementsHandler:

    """
    Contains tools to extract and check requirements of a module.
    """

    module_filepath = attr.ib(default=None)

    package_mappings = attr.ib(default={}, type = dict)
    requirements_output_path  = attr.ib(default='./')
    output_requirements_prefix = attr.ib(default="requirements_")
    custom_modules_filepath = attr.ib(default=None)
    add_header = attr.ib(default=True, type = bool)
    python_version = attr.ib(default='3.8')

    # output
    module_name = attr.ib(init=False)
    requirements_list = attr.ib(default=[], type = list)
    optional_requirements_list = attr.ib(default=[], type = list)
    vulnerabilities = attr.ib(default=[], type = list)

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Package Requirements Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        self.vulnerabilities = []
        self.requirements_list = []


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _keep_most_constrained(self, requirements : list):

        try:
            # Regex to capture the package name, extras, version operator, and version
            pattern = re.compile(r"(\S+?)(?:\[(\w+)\])?(?:(==|>=|<=|>|<)\s*([\d\.]+))?$")

            # Dictionary to hold the most constrained version for each package
            package_constraints = {}

            for req in requirements:
                match = pattern.match(req)
                if match:
                    pkg_name, extra, operator, ver = match.groups()

                    # Create a tuple representing the constraint: (extras, operator, version)
                    constraint = (extra, operator, ver)

                    # If the package is not already in the dictionary, or if the new requirement has more constraints
                    if pkg_name not in package_constraints:
                        package_constraints[pkg_name] = (req, constraint)
                    else:
                        # Extract the current best requirement
                        current_req, current_constraint = package_constraints[pkg_name]

                        # Compare the number of constraints
                        new_constraints_count = sum(x is not None for x in constraint)
                        current_constraints_count = sum(x is not None for x in current_constraint)

                        if new_constraints_count > current_constraints_count:
                            package_constraints[pkg_name] = (req, constraint)
                        elif new_constraints_count == current_constraints_count:
                            # If they have the same number of constraints, compare versions
                            if ver and current_constraint[2]:
                                if version.parse(ver) > version.parse(current_constraint[2]):
                                    package_constraints[pkg_name] = (req, constraint)

            # Return the most constrained requirements
            requirements = [req for req, _ in package_constraints.values()]
            return requirements
        except Exception as e:
            return requirements

    def check_vulnerabilities(self,
                              requirements_list : list = None,
                              raise_error : bool = True):

        """
        Checks vulnerabilities with pip-audit
        """

        if requirements_list is None:
            requirements_list = self.requirements_list + self.optional_requirements_list


        # Create a temporary requirements file
        with tempfile.NamedTemporaryFile(delete=True, mode='w', suffix='.txt') as temp_req_file:
            for dep in requirements_list:
                temp_req_file.write(dep + '\n')
            temp_req_file.flush()

            # Run pip-audit on the temporary requirements file
            result = subprocess.run(
                ["pip-audit", "-r", temp_req_file.name, "--progress-spinner=off"],
                capture_output=True, text=True
            )

            print(result.stdout)
            self.logger.info(result.stderr)

            if result.returncode == 0:
                vulnerabilities = []
            else:

                if result.stdout:
                    # Access stdout
                    stdout = result.stdout.strip()

                    # Split into lines and skip the header (assumed to be the first two lines here)
                    lines = stdout.splitlines()
                    header_line = ['name', 'version', 'id', 'fix_versions']
                    data_lines = lines[2:]

                    # Prepare a list of dictionaries
                    vulnerabilities = []

                    # Process each data line into a dictionary
                    for line in data_lines:
                        values = line.split()

                        vd = {key:value for key,value in zip(header_line, values)}
                        if len(values) <= 3:
                            vd['fix_versions'] = None

                        vulnerabilities.append(vd)
                else:
                    vulnerabilities = []

        self.vulnerabilities += vulnerabilities

        if vulnerabilities and raise_error:
            raise ValueError("Found vulnerabilities, resolve them or ignore check to move forwards!")

    def list_custom_modules(self,
                            custom_modules_filepath : str = None):
        """
        List all custom module names in the specified directory.
        """

        if custom_modules_filepath is None:
            custom_modules_filepath = self.custom_modules_filepath

        if custom_modules_filepath is None:
            return []

        custom_modules = set()

        if custom_modules_filepath is None:
            self.logger.warning("No custom modules path was provided! Returning empty list!")
        else:
            for filename in os.listdir(custom_modules_filepath):
                if filename.endswith('.py') and not filename.startswith('__'):
                    module_name = filename.rsplit('.', 1)[0]
                    custom_modules.add(module_name)

        return list(custom_modules)

    def is_standard_library(self,
                            module_name : str,
                            python_version : str = None):

        """
        Check if a module is part of the standard library for the given Python version.
        """

        if python_version is None:
            python_version = self.python_version

        return module_name in stdlib_list(python_version)


    def read_requirements_file(self,
                               requirements_filepath : str) -> list:

        """
        Read requirements file and output a list.
        """


        with open(requirements_filepath, 'r') as file:
            requirements = [line.strip() for line in file if line.strip() and not line.startswith('#')]

        return requirements

    def extract_requirements(self,
                             module_filepath : str = None,
                             custom_modules : list = None,
                             package_mappings : dict = None,
                             python_version : str = None,
                             add_header : bool = None):

        """
        Extract requirements from the module.
        """

        if module_filepath is None:

            if self.module_filepath is None:
                raise ValueError("Parameter 'module_filepath' was not probided!")

            module_filepath = self.module_filepath

        if custom_modules is None:
            custom_modules = self.list_custom_modules()

        if package_mappings is None:
            package_mappings = self.package_mappings

        if python_version is None:
            python_version = self.python_version

        if add_header is None:
            add_header = self.add_header

        file_path = module_filepath
        module_name = os.path.basename(module_filepath)

        self.module_name = module_name

        # Matches 'import module as alias' with optional version comment
        #import_pattern_as = re.compile(r"import (\S+)(?: as (\S+))?(?:\s+#(?:\s*(==|>=|<=|>|<)\s*([0-9.]+)))?")
        import_pattern_as = re.compile(
            r"import (\S+)(?: as (\S+))?(?:\s+#(?:\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([0-9.]+))?)?")

        # Separate regex patterns for 'import' and 'from ... import ...' statements
        import_pattern = re.compile(
            r"import (\S+)(?:\s+#(?:\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([0-9.]+))?)?")

        #from_import_pattern = re.compile(r"from (\S+) import [^#]+#\s*(==|>=|<=|>|<)\s*([0-9.]+)")
        from_import_pattern = re.compile(
            r"from (\S+) import ([\w\s,]+)(?:\s*#(?:\[(\w+)\])?\s*(==|>=|<=|>|<)\s*([0-9.]+))?"
        )

        # optional requirements
        optional_import_pattern_as = re.compile(
            r"#! import (\S+)(?: as (\S+))?(?:\s+#(?:\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([0-9.]+))?)?")
        optional_import_pattern = re.compile(
            r"#!\s*import\s+(\S+)(?:\s+#(?:\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([\d\.]+))?)?"
        )
        optional_from_import_pattern = re.compile(
            r"#!\s*from\s+(\S+)\s+import\s+([\w\s,]+)(?:\s*#(?:\s*\[(\w+)\])?(?:\s*(==|>=|<=|>|<)\s*([0-9.]+))?)?"
        )

        #manual_addition_pattern = re.compile(r"^#@\s*(.*)")


        requirements = []
        optional_requirements = []
        manual_additions = []
        if add_header:
            new_header = [f'### {module_name}']
        else:
            new_header = []

        with open(file_path, 'r') as file:
            for line in file:

                if "#-" in line:
                    continue

                if line.startswith("#@") and line.replace("#@", "").strip():
                    manual_additions.append(line.replace("#@", "").strip())
                    continue

                # manual_addition_match = manual_addition_pattern.search(line)
                # if manual_addition_match and manual_addition_match.group(1).strip():
                #     manual_additions.append(manual_addition_match.group(1).strip())
                #     continue


                import_match = import_pattern.match(line)
                from_import_match = from_import_pattern.match(line)
                import_as_match = import_pattern_as.match(line)

                optional_import_match = optional_import_pattern.match(line)
                optional_from_import_match = optional_from_import_pattern.match(line)
                optional_import_as_match = optional_import_pattern_as.match(line)

                module = None
                optional_module = None

                if import_as_match:
                    module, alias, extra_require, version_constraint, version = import_as_match.groups()
                elif from_import_match:
                    module, _, extra_require, version_constraint, version = from_import_match.groups()
                elif import_match:
                    module, extra_require, version_constraint, version = import_match.groups()
                elif optional_import_match:
                    optional_module, optional_extra_require, optional_version_constraint, optional_version = optional_import_match.groups()
                elif optional_from_import_match:
                    optional_module, _, optional_extra_require, optional_version_constraint, optional_version = optional_from_import_match.groups()
                elif optional_import_as_match:
                    optional_module, optional_alias, optional_extra_require, optional_version_constraint, optional_version = optional_import_as_match.groups()
                else:
                    continue

                skip = False

                if module:

                    # Skip local imports
                    if module.startswith('.'):
                        skip = True

                    if not skip:

                        # Extract the base package name
                        module_root = module.split('.')[0]
                        # Extracting package import leaf
                        module_leaf = module.split('.')[-1]

                    # Skip standard library and custom modules
                    if self.is_standard_library(module_root, python_version) or module_root in custom_modules \
                        or self.is_standard_library(module_leaf, python_version) or module_leaf in custom_modules:
                        skip = True

                    if not skip:

                        # Use the mapping to get the correct package name
                        module = package_mappings.get(module_root, module_root)

                        extra_require_ad = f"[{extra_require}]" if extra_require else ""
                        version_info = f"{version_constraint}{version}" if version_constraint and version else ""

                        if version_info:
                            requirements.append(f"{module}{extra_require_ad}{version_info}")
                        else:
                            requirements.append(f"{module}{extra_require_ad}")

                        # deduplicate requirements
                        requirements = [requirements[0]] + list(set(requirements[1:]))

                skip = False

                if optional_module:

                    # Skip local imports
                    if optional_module.startswith('.'):
                        skip = True

                    if not skip:

                        # Extract the base package name
                        module_root = optional_module.split('.')[0]
                        # Extracting package import leaf
                        module_leaf = optional_module.split('.')[-1]

                    # Skip standard library and custom modules
                    if self.is_standard_library(module_root, python_version) or module_root in custom_modules \
                        or self.is_standard_library(module_leaf, python_version) or module_leaf in custom_modules:
                        skip = True

                    if not skip:

                        # Use the mapping to get the correct package name
                        optional_module = package_mappings.get(module_root, module_root)

                        optional_extra_require_ad = f"[{optional_extra_require}]" if optional_extra_require else ""
                        optional_version_info = f"{optional_version_constraint}{optional_version}" \
                            if optional_version_constraint and optional_version else ""

                        if optional_version_info:
                            optional_requirements.append(f"{optional_module}{optional_extra_require_ad}{optional_version_info}")
                        else:
                            optional_requirements.append(f"{optional_module}{optional_extra_require_ad}")

        if self.requirements_list:
            header = [self.requirements_list.pop(0)]
        else:
            header = []

        # Include manual additions in the final list
        requirements.extend(manual_additions)

        requirements_list = header + new_header + list(set(self.requirements_list + requirements))
        optional_requirements_list = list(set(self.optional_requirements_list + optional_requirements))

        requirements_list = self._keep_most_constrained(requirements_list)
        optional_requirements_list = self._keep_most_constrained(optional_requirements_list)

        self.requirements_list = requirements_list
        self.optional_requirements_list = optional_requirements_list

        return requirements_list, optional_requirements_list

    def write_requirements_file(self,
                                module_name : str = None,
                                requirements : list = None,
                                output_path : str = None,
                                prefix : str = None):

        """
        Save extracted requirements.
        """

        if module_name is None:
            module_name = self.module_name

        if requirements is None:
            requirements = self.requirements_list

        if output_path is None:
            output_path = os.path.dirname(self.requirements_output_path)

        if prefix is None:
            prefix = self.output_requirements_prefix

        output_file = os.path.join(output_path, f"{prefix}{module_name}.txt")

        with open(output_file, 'w') as file:
            for req in requirements:
                file.write(req + '\n')