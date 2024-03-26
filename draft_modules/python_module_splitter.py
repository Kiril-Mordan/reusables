"""
Python Module Splitter and Analyzer

This module provides functionality to analyze and split Python code files into
smaller segments based on class definitions. It leverages the Abstract Syntax Tree (AST)
for parsing and analysis, allowing for detailed inspection of function definitions, call chains,
and class structures within the module.

"""


import attr
import ast
import logging


@attr.s
class PythonCodeAnalyzer(ast.NodeVisitor):

    """
    A class to analyze Python code files for various aspects such as defined functions,
    call chains within those functions, and class definitions. It leverages the AST
    (Abstract Syntax Tree) module to parse and visit nodes in the syntax tree of a Python file.

    Attributes
    ----------
    filename : str
        The path to the Python file to be analyzed.
    logger : logging.Logger, optional
        Custom logger for logging information. If not provided, a new logger will be initialized.
    logger_name : str, optional
        The name of the logger to use or initialize. Default is 'Python Code Analyzer'.
    loggerLvl : logging.Level, optional
        The logging level for the logger. Default is logging.INFO.
    logger_format : str, optional
        The logging format to use for the logger. Default is None, which uses the basic logging format.
    defined_functions : set
        A set of names of all functions and methods defined in the analyzed file. Populated after file parsing.
    call_chains : dict
        A dictionary mapping function names to lists of functions they call. Populated after file parsing.
    classes : dict
        A dictionary mapping class names to lists of their method names. Populated after file parsing.


    """

    filename = attr.ib()

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Python Code Analyzer')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)


    def __attrs_post_init__(self):
        self._initialize_logger()

        self.defined_functions = set()  # Stores names of defined functions and methods
        self.call_chains = {}  # Stores call chains
        self.classes = {}

        # Initialize with None to know when we're not in a class
        self.current_class = None
        # Adjusted to store functions and their call chains within classes
        self.class_function_chains = {}

    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def visit_FunctionDef(self, node):

        """
        Visits FunctionDef nodes in the AST. It registers the function's name, adds it to the set of
        defined functions, and tracks the call chain within the function.

        Parameters
        ----------
        node : ast.FunctionDef
            The node representing a function definition in the AST.
        """

        function_name = node.name
        self.defined_functions.add(function_name)
        self.call_chains[function_name] = self._find_function_calls(node)
        self.generic_visit(node)

        function_name = node.name
        if self.current_class:
            # If within a class, add function to the current class's dictionary
            calls = self._find_function_calls(node, class_name = self.current_class)
            self.class_function_chains[self.current_class][function_name] = calls
        self.generic_visit(node)

    # def _find_function_calls(self, node, class_name = None):
    #     calls = []
    #     for n in ast.walk(node):
    #         if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name)):
    #             called_func_name = self._resolve_function_name(n.func)
    #             if class_name is not None:
    #                 called_func_name + f"{class_name}.{called_func_name}"
    #             calls.append(called_func_name)
    #     return calls

    def visit_ClassDef(self, node):

        """
        Visits ClassDef nodes in the AST. It registers the class's name and stores the names of its methods.

        Parameters
        ----------
        node : ast.ClassDef
            The node representing a class definition in the AST.
        """

        class_name = node.name

        self.current_class = class_name
        self.class_function_chains[class_name] = {}

        self.classes[class_name] = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.classes[class_name].append(item.name)
        self.generic_visit(node)

    def _find_function_calls(self, node, class_name = None):

        """
        Identifies and returns function calls within a given node. It checks if the function called
        is defined within the file and adds it to the call chain.

        Parameters
        ----------
        node : ast.Node
            The node to search for function calls within.

        Returns
        -------
        list of str
            A list of names of functions called within the node.
        """

        calls = []
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name)):
                called_func_name = ''
                if isinstance(n.func, ast.Attribute):
                    if isinstance(n.func.value, ast.Name) and n.func.value.id == 'self':
                        called_func_name = n.func.attr
                elif isinstance(n.func, ast.Name):
                    called_func_name = n.func.id

                if called_func_name in self.defined_functions:
                    if class_name:
                        called_func_name = f"{class_name}.{called_func_name}"
                    calls.append(called_func_name)
        return calls

    def parse_file(self):

        """
        Parses the Python file specified by `filename`, visiting nodes to collect information on
        function definitions, call chains, and class definitions.
        """

        with open(self.filename, 'r') as file:
            source_code = file.read()
        tree = ast.parse(source_code)
        self.visit(tree)

    def report(self):

        """
        Prints a report of the function call chains and class method definitions found in the file.
        """

        print("Function Call Chains:")
        for func, calls in self.call_chains.items():
            print(f"{func} calls: {', '.join(calls) if calls else 'None'}")


@attr.s
class PythonModuleSplitter:

    """
    A class designed to split Python modules into smaller parts based on class definitions,
    optionally including or excluding docstrings and class headers from the output.

    This class is useful for processing and analyzing Python code at a granular level,
    especially when working with large modules.

    Attributes
    ----------
    module_path : str, optional
        Path to the Python module file to be split. Default is None.
    include_docstrings : bool, optional
        Flag to include docstrings in the output. Default is True.
    include_class_header : bool, optional
        Flag to include the class header in the output. Default is True.
    module_content : str
        The content of the Python module file as a string. This attribute is initialized after the class is instantiated.
    module_content_no_docstring : str
        The content of the Python module file as a string, with docstrings removed. This attribute is initialized after the class is instantiated.
    logger : logging.Logger, optional
        Custom logger for logging information. Default is None, which causes the class to initialize a new logger.
    logger_name : str, optional
        Name of the logger to be initialized if no custom logger is provided. Default is 'Python Module Splitter'.
    loggerLvl : logging.LEVEL, optional
        Logging level for the logger. Default is logging.INFO.
    logger_format : str, optional
        Logging format for the logger. Default is None, which uses the basic logging format.

    """

    module_path = attr.ib(default=None, type = str)
    module_content = attr.ib(default=None, type = str)
    module_content_no_docstring = attr.ib(default=None, type = str)

    class_function_chains = attr.ib(default=None)

    include_docstrings = attr.ib(default = True, type = bool)
    include_class_header = attr.ib(default = True, type = bool)

    # # dependancy
    # module_analyser_class = attr.ib(default=PythonCodeAnalyzer)

    # # activated dependacies
    # module_analyser = attr.ib(init=False)


    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Python Module Splitter')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()
        if self.module_path:
            self.get_module_code()

    # def _initialize_module_analyzer(self):



    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def get_module_code(self, module_path : str = None):

        if module_path is None:
            module_path = self.module_path
            return_content = False
        else:
            return_content = True

        if module_path is None:
            raise ValueError("Module was not provided!")

        with open(module_path, 'r') as file:
            module_content = file.read()

        self._remove_docstrings(module_content = module_content)

        self.module_content = module_content

        if return_content:
            return module_content

    def _remove_docstrings(self, module_content : str = None):

        if module_content is None:
            module_content = self.module_content

        class DocstringRemover(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                """Strip docstring from a function definition."""
                self.generic_visit(node)
                if ast.get_docstring(node):
                    node.body = node.body[1:]
                return node

            def visit_ClassDef(self, node):
                """Strip docstring from a class definition."""
                self.generic_visit(node)
                if ast.get_docstring(node):
                    node.body = node.body[1:]
                return node

        parsed_tree = ast.parse(module_content)
        docstring_remover = DocstringRemover()
        modified_tree = docstring_remover.visit(parsed_tree)
        self.module_content_no_docstring =  ast.unparse(modified_tree)

    def _add_function_chains(self,
                             class_code : str,
                            class_name : str,
                            function_name : str,
                            class_function_chains : dict,
                            include_extended_chains : bool = True) -> str:

        """
        Adding function chains context to chunk
        """

        class_function_chains = class_function_chains.copy()

        chains = class_function_chains[class_name][function_name]
        chunk_code = ''

        if len(chains) > 0:
            chunk_code = "Function chains: " + "\n\n" + " -> " + \
                str(chains)


        if include_extended_chains:
            chains = class_function_chains[class_name][function_name]

            if len(chains) > 0:

                chunk_code = chunk_code + "\n\n" + "Function chain details: "

            for function in chains:

                class_name = function.split(".")[0]

                function_name = ".".join(function.split(".")[1:])

                function_chain = class_function_chains[class_name][function_name]

                chunk_code = chunk_code + "\n" + function + " -> " + str(function_chain)

        chunk_code = chunk_code + "\n\n" + \
                class_code

        return chunk_code


    def split_text(self,
                   text : str = None,
                   class_function_chains : dict = None,
                   include_docstrings: bool = None,
                   include_class_header : bool = None):

        if include_docstrings is None:
            include_docstrings = self.include_docstrings

        if include_class_header is None:
            include_class_header = self.include_class_header

        if class_function_chains is None:
            class_function_chains = self.class_function_chains

        if text is None:

            if include_docstrings:
                module_content = self.module_content
            else:
                module_content = self.module_content_no_docstring
        else:
            module_content = text


        tree = ast.parse(module_content)
        class_definitions = [node for node in tree.body if isinstance(node, ast.ClassDef)]

        segments = {}
        chunks = []
        for class_def in class_definitions:

            segments[class_def.name] = {}

            if include_class_header:

                # Find the first method
                first_method_index = next((i for i, n in enumerate(class_def.body) if isinstance(n, ast.FunctionDef)), None)

                # If there's no method, continue to next class
                if first_method_index is None:
                    continue

                # Everything before the first method
                pre_method_body = class_def.body[:first_method_index]


            for method in [n for n in class_def.body if isinstance(n, ast.FunctionDef)]:

                body_code = []
                if include_class_header:
                    # Class body consists of pre-method part and the current method
                    body_code = pre_method_body
                body_code = body_code + [method]

                class_copy = ast.ClassDef(name=class_def.name,
                                        bases=class_def.bases,
                                        keywords=class_def.keywords,
                                        body=body_code,
                                        decorator_list=class_def.decorator_list)
                class_code = ast.unparse(class_copy)

                # if class function chains provided
                if class_function_chains:

                    class_code = self._add_function_chains(class_code = class_code,
                                                           class_name = class_def.name,
                                                           function_name = method.name,
                                                           class_function_chains = class_function_chains)

                chunks.append(class_code)
                segments[class_def.name][method.name] = class_code

        self.segments = segments

        return chunks
