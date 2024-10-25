import logging
import os
import ast
import json
import attr #>=22.2.0
import difflib
import importlib
import importlib.metadata
import importlib.resources as pkg_resources

@attr.s
class DependenciesAnalyser:

    """
    Contains set of tools to check package dependencies.
    """

    package_name = attr.ib(default=True)
    base_mapping_filepath = attr.ib(default=None)
    package_licenses_filepath = attr.ib(default=None)
    allowed_licenses = attr.ib(default=[])

    package_licenses = attr.ib(default=None)

    standard_licenses = attr.ib(default=[
            "mit", "bsd-3-clause", "bsd-2-clause", "apache-2.0",
            "gpl-3.0", "lgpl-3.0", "mpl-2.0", "agpl-3.0", "epl-2.0"
        ])

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Dependencies Analyser')
    loggerLvl = attr.ib(default=logging.DEBUG)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        if self.allowed_licenses is None:
            self.allowed_licenses = self.standard_licenses
            self.allowed_licenses.append('-')

    def _initialize_logger(self):
        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _extract_dependencies_names(self, requirements : list):

        reqs = [req.split(" ")[0]\
            .split("==")[0]\
                .split("<=")[0]\
                    .split("<")[0]\
                        .split(">=")[0]\
                            .split(">")[0]\
                                .split(";")[0] \
            for req in requirements if 'extra ==' not in req]

        return reqs

    def _get_licenses(self,
                      dependencies : list,
                      package_licenses : dict = None,
                      normalize : bool = True):

        if package_licenses is None:
            package_licenses = self.package_licenses

        if package_licenses is None:
            package_licenses = self.load_package_mappings()

        licenses = {}
        for req in dependencies:
            try:
                license_ = self.get_package_metadata(req)['license_label']
                if license_:
                    if normalize:
                        license_ = self._normalize_license_label(license_)
                    else:
                        license_ = license_[0:50]
                else:
                    license_ = '-'
            except Exception as e:
                license_ = '-'

            if license_ == 'unknown':
                license_ = package_licenses.get(req, 'unknown')
            if license_ == '-':
                license_ = package_licenses.get(req, '-')

            licenses[req] = license_

        return licenses

    def _count_keys(self, d):
        if isinstance(d, dict):
            return len(d) + sum(self._count_keys(v) for v in d.values() if isinstance(v, dict))
        return 0

    def _apply_to_lists(self, data, func):
        for key, value in data.items():
            if isinstance(value, list):
                # Apply the function to the list
                data[key] = func(value)
            elif isinstance(value, dict):
                # Recursively go deeper into the dictionary
                self._apply_to_lists(value, func)
            # If value is neither list nor dict, do nothing

    def _extract_dependencies_layer(self, dependencies):

        if dependencies == []:
            return dependencies

        requirements_dict = self.extract_requirements_for_dependencies(
            dependencies = dependencies
        )
        dependencies_dict = {dep : self._extract_dependencies_names(reqs_) \
            for dep, reqs_ in requirements_dict.items()}

        return dependencies_dict

    def _flatten_dict_with_subtrees(self, d, parent_key=''):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            # Add subtree or package
            items.append(new_key)

            if isinstance(v, dict):
                # Recursively flatten subtrees
                items.extend(self._flatten_dict_with_subtrees(v, new_key))
            else:
                for item in v:
                    # Add individual packages
                    items.append(f"{new_key}.{item}")
        return items

    def load_package_mappings(self,
                              mapping_filepath : str = None,
                              base_mapping_filepath : str = None):
        """
        Get file with mappings of package license labels.
        """

        if base_mapping_filepath is None:
            base_mapping_filepath = self.base_mapping_filepath

        if base_mapping_filepath is None:

            # with pkg_resources.path('package_auto_assembler','.') as path:
            #     paa_path = path

            paa_path = pkg_resources.files('package_auto_assembler')

            if 'artifacts' in os.listdir(paa_path):

                with pkg_resources.path('package_auto_assembler.artifacts',
                'package_licenses.json') as path:
                    base_mapping_filepath = path

                with open(base_mapping_filepath, 'r') as file:
                    base_package_licenses = json.load(file)
            else:
                base_package_licenses = {}

        if mapping_filepath is None:
            mapping_filepath = self.package_licenses_filepath

        if mapping_filepath is None:
            self.logger.debug("No package mapping provided")
            package_licenses = {}
        else:
            with open(mapping_filepath, 'r') as file:
                package_licenses = json.load(file)

        base_package_licenses.update(package_licenses)

        self.package_licenses = base_package_licenses

        return base_package_licenses

    def extract_dependencies_tree(self,
                                    package_name : str = None,
                                    requirements : list = None,
                                    layers : int = 100):

        """
        Extracts dependencies tree for a package.
        """

        if package_name is None:
            package_name = self.package_name

        if package_name is None:
            raise ValueError(f"Provide package_name!")

        if requirements is None:

            requirements = self.get_package_requirements(
                package_name = package_name
            )

        if requirements:

            dependencies = self._extract_dependencies_names(
                requirements=requirements)

            dependencies_dict = self._extract_dependencies_layer(
                dependencies = dependencies)

            if layers == 1:
                return dependencies_dict


            for layer in range(layers):
                list_dim0 = self._count_keys(dependencies_dict)
                self._apply_to_lists(data = dependencies_dict,
                            func = self._extract_dependencies_layer)

                list_dim = self._count_keys(dependencies_dict)

                if list_dim == list_dim0:
                    break
        else:
            dependencies_dict = {}


        return dependencies_dict

    def add_license_labels_to_dep_tree(self,
                                        dependencies_tree : dict,
                                        normalize : bool = True):

        """
        Adds license labels to dependencies tree.
        """

        flattened_tree_deps = self._flatten_dict_with_subtrees(
            dependencies_tree)

        tree_dep_license = {ft : self._get_licenses([ft.split('.')[-1]],
        normalize = normalize)[ft.split('.')[-1]] \
            for ft in flattened_tree_deps}

        return tree_dep_license

    def find_unexpected_licenses_in_deps_tree(self,
                                            tree_dep_license : dict,
                                            allowed_licenses : list = None,
                                            raise_error : bool = True):

        """
        Returns a dictionary of packages that contained unexpected license labels.
        If raise error is True, prints portion of dependencies tree.
        """

        if allowed_licenses is None:
            allowed_licenses = self.allowed_licenses


        out = {dep : license_label \
            for dep, license_label in tree_dep_license.items() \
                if license_label not in allowed_licenses}

        requirements = list(set([req.split('.')[0] for req in out \
            if req.split('.')[0] == req]))

        tree_missing_links_update = {req.split('.')[0] : '' \
            for req in out if req.split('.')[0] not in requirements}


        for req_from_missing in tree_missing_links_update:

            tree_partials = {req : license_label \
                for req, license_label in out.items() \
                    if req.split('.')[0] == req_from_missing}

            for req_part in tree_partials:
                del out[req_part]

            out[req_from_missing] = tree_missing_links_update[req_from_missing]
            out.update(tree_partials)

        if raise_error and out != {}:
            self.print_flattened_tree(flattened_dict = out)
            raise Exception("Found unexpected licenses!")
        else:
            self.logger.info("No unexpected licenses found")

        return out

    def print_flattened_tree(self, flattened_dict):
        """
        Prints provided dependencies tree with provided values.
        """

        def recursive_build_tree(full_key, value, current_level):
            keys = full_key.split(".")
            for key in keys[:-1]:
                if key not in current_level:
                    current_level[key] = {}
                elif isinstance(current_level[key], str):
                    # If it's a string, convert it into a dictionary to store the nested structure
                    current_level[key] = {"_value": current_level[key]}
                current_level = current_level[key]
            # Store the value, handle if it's at a nested level or the root
            if keys[-1] in current_level and isinstance(current_level[keys[-1]], dict):
                current_level[keys[-1]]["_value"] = value
            else:
                current_level[keys[-1]] = value

        tree = {}
        for full_key, value in flattened_dict.items():
            recursive_build_tree(full_key, value, tree)

        def recursive_print(d, indent=0, is_last=False):
            for i, (key, value) in enumerate(d.items()):
                is_last_item = i == len(d) - 1
                prefix = "└── " if is_last_item else "├── "
                if isinstance(value, dict):
                    # Check if there is a _value to print as the value of this key
                    if "_value" in value:
                        print("    " * indent + prefix + key + f" : {value['_value']}")
                    else:
                        print("    " * indent + prefix + key + " : -")
                    recursive_print({k: v for k, v in value.items() if k != "_value"}, indent + 1, is_last_item)
                else:
                    print("    " * indent + prefix + key + f" : {value}")

        # Start printing the tree, avoiding extra _value printing at the root level
        for key, value in tree.items():
            if isinstance(value, dict) and "_value" in value:
                print(f"└── {key} : {value['_value']}")
                recursive_print({k: v for k, v in value.items() if k != "_value"}, indent=1)
            else:
                print(f"└── {key} : {value}")


    def extract_requirements_for_dependencies(self, dependencies : list):

        """
        Outputs a dictionary where key is dependency and value is
        a list of requirements for that dependency.
        """

        requirements_dict = {dep : self.get_package_requirements(
            package_name = dep
        ) for dep in dependencies}

        return requirements_dict

    def filter_packages_by_tags(self, tags : list):

        """
        Uses list of provided tags to search though installed
        dependencies and returns of names of those that match.
        """

        import pkg_resources
        matches = []
        for dist in pkg_resources.working_set:
            try:
                metadata_lines = dist.get_metadata_lines('METADATA')
                if all(any(tag in line for line in metadata_lines) for tag in tags):
                    matches.append((dist.project_name, dist.version))
            except (FileNotFoundError, KeyError):
                continue
        return matches


    def get_package_metadata(self, package_name : str = None):

        """
        Returns some preselected metadata fields if available, like:

            - keywords
            - version
            - author
            - author_email
            - classifiers
            - paa_version
            - paa_cli
            - license_label

        for provided package name.
        """

        if package_name is None:
            package_name = self.package_name

        if package_name is None:
            raise ValueError(f"Provide package_name!")

        import pkg_resources
        dist = pkg_resources.get_distribution(package_name)
        metadata = dist.get_metadata_lines('METADATA')

        try:
            version = dist.version
        except Exception as e:
            version = None

        keywords = None
        author = None
        author_email = None
        paa_version = None
        paa_cli = False
        classifiers = []
        license_label = None

        for line in metadata:
            if line.startswith("Keywords:"):
                keywords = ast.literal_eval(line.split("Keywords: ")[1])
            if line.startswith("Author:"):
                author = line.split("Author: ")[1]
            if line.startswith("Author-email:"):
                author_email = line.split("Author-email: ")[1]
            if line.startswith("Classifier:"):
                classifiers.append(line.split("Classifier: ")[1])
            # if line.startswith("Classifier: PAA-Version ::"):
            #     paa_version = line.split("Classifier: PAA-Version :: ")[1]
            # if line.startswith("Classifier: PAA-CLI ::"):
            #     paa_cli = line.split("Classifier: PAA-CLI :: ")[1]
            if line.startswith("License:"):
                license_label = line.split("License: ")[1]

        return {'keywords' : keywords,
                'version' : version,
                'author' : author,
                'author_email' : author_email,
                'classifiers' : classifiers,
                'paa_version' : paa_version,
                'paa_cli' : paa_cli,
                'license_label' : license_label}

    def get_package_requirements(self, package_name : str = None):

        """
        Returns a list of requirements for provided package name.
        """

        if package_name is None:
            package_name = self.package_name

        if package_name is None:
            raise ValueError(f"Provide package_name!")

        try:
            metadata = importlib.metadata.metadata(package_name)
            requirements = metadata.get_all("Requires-Dist", [])
            if requirements != []:
                requirements = requirements
        except Exception as e:
            self.logger.debug(f'No requirements found for {package_name}')
            requirements = []

        return requirements

    def _normalize_license_label(self,
                                license_label : str,
                                standard_licenses : list = None):

        """
        For provided license label, attempts to match it with the following names:

            "mit", "bsd-3-clause", "bsd-2-clause", "apache-2.0", "gpl-3.0", "lgpl-3.0",
            "mpl-2.0", "agpl-3.0", "epl-2.0"

        and if nothing matches returns "unknown"
        """

        if standard_licenses is None:
            standard_licenses = self.standard_licenses

        if "bsd-3-clause" in standard_licenses:
            standard_licenses.append("new bsd")

        if license_label is None:
            return "unknown"

        # Normalize to lowercase
        normalized_label = license_label.lower()

        normalized_label = normalized_label.replace('software license', '')

        # Match with the highest similarity
        match = difflib.get_close_matches(normalized_label, standard_licenses, n=1, cutoff=0.4)

        license_label = match[0] if match else "unknown"

        # remapping licenses
        if license_label == "new bsd":
            license_label = "bsd-3-clause"

        return license_label
