import logging
import os
import sys
import shutil
import attr #>=22.2.0
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

@attr.s
class FastApiHandler:

    """
    Contains set of tools to prepare and handle api routes for packages.
    """

    # inputs
    fastapi_routes_filepath = attr.ib(default = None)
    setup_directory = attr.ib(default = None)

    docs_prefix = attr.ib(default = "/mkdocs")

    # processed
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='FastAPI Handler')
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

    def _include_docs(self,
                      app,
                      docs_paths,
                      docs_prefix = None):

        if docs_prefix is None:
            docs_prefix = self.docs_prefix

        i_str = ''
        i = 0
        for docs_path in docs_paths:
            app.mount(f"{docs_prefix}{i_str}",
                      StaticFiles(directory=docs_path,
                                  html=True))
            i += 1
            i_str = str(i)


        return app

    def _include_package_routes(self,
                                app,
                                package_names : list,
                                routes_paths : list):


        for package_name in package_names:
            try:

                package_name = package_name.replace('-','_')

                # Import the package
                package = importlib.import_module(package_name)

                # Get the package's directory
                package_dir = os.path.dirname(package.__file__)

                # Construct the path to routes.py
                routes_file_path = os.path.join(package_dir, 'routes.py')

                # Construct the path to site
                docs_file_path = os.path.join(package_dir,'mkdocs', 'site')

                if os.path.exists(routes_file_path):
                    routes_module = importlib.import_module(f"{package_name}.routes")
                    app.include_router(routes_module.router)

                if os.path.exists(docs_file_path):
                    app = self._include_docs(
                        app = app,
                        docs_paths = [docs_file_path],
                        docs_prefix = f"/{package_name.replace('_','-')}/docs"
                    )

            except ImportError as e:
                print(e)
                self.logger.error(f"Error importing routes from {package_name}: {e}")
                sys.exit(1)

        for routes_path in routes_paths:
            try:
                # Generate a module name from the file path
                module_name = routes_path.rstrip('.py').replace('/', '.').replace('\\', '.')

                # Load the module from the specified file path
                spec = importlib.util.spec_from_file_location(module_name, routes_path)
                if spec is None:
                    print(f"Could not load spec from {routes_path}")
                    sys.exit(1)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Check if the module has a 'router' attribute
                if hasattr(module, 'router'):
                    app.include_router(module.router)
                else:
                    print(f"The module at {routes_path} does not have a 'router' attribute.")
                    sys.exit(1)
            except FileNotFoundError:
                print(f"File not found: {routes_path}")
                sys.exit(1)
            except Exception as e:
                print(f"Error loading routes from {routes_path}: {e}")
                sys.exit(1)

        return app

    def prepare_routes(self,
                       fastapi_routes_filepath: str = None,
                       setup_directory : str = None):

        """
        Prepare fastapi routes for packaging.
        """

        if fastapi_routes_filepath is None:
            fastapi_routes_filepath = self.fastapi_routes_filepath

        if setup_directory is None:
            setup_directory = self.setup_directory

        if fastapi_routes_filepath is None:
            raise ImportError("Parameter fastapi_routes_filepath is missing!")

        if setup_directory is None:
            raise ImportError("Parameter setup_directory is missing!")

        # Copying module to setup directory
        shutil.copy(fastapi_routes_filepath,
                    os.path.join(setup_directory, "routes.py"))

        return True

    def run_app(self,
                description : dict = None,
                middleware : dict = None,
                run_parameters : dict = None,
                package_names : list = None,
                routes_paths : list = None,
                docs_paths : list = None):

        """
        Sets up FastAPI app with provided `description` and runs it with
        routes for selected `package_names` and `routes_paths`
        with `run_parameters`.
        """

        if description is None:
            description = {}

        if package_names is None:
            package_names = []

        if routes_paths is None:
            routes_paths = []

        if run_parameters is None:
            run_parameters = {
                "host" : "0.0.0.0",
                "port" : 8000
            }
        else:
            if run_parameters.get("port"):
                run_parameters["port"] = int(run_parameters["port"])

        app = FastAPI(**description)

        if middleware is not None:
            app.add_middleware(
                CORSMiddleware,
                **middleware
            )

        if docs_paths:
            app = self._include_docs(
                app = app,
                docs_paths = docs_paths
            )

        app = self._include_package_routes(
            app = app,
            package_names = package_names,
            routes_paths = routes_paths)

        uvicorn.run(app, **run_parameters)

    def extract_routes_from_package(self,
                              package_name : str,
                              output_directory : str = None,
                              output_filepath : str = None):
        """
        Extracts the `routes.py` file from the specified package.
        """
        try:

            if output_directory is None:
                output_directory = '.'

            # Import the package
            package = importlib.import_module(package_name)

            # Get the package's directory
            package_dir = os.path.dirname(package.__file__)

            # Construct the path to routes.py
            routes_file_path = os.path.join(package_dir, 'routes.py')
            if not os.path.exists(routes_file_path):
                print(f"No routes.py found in package '{package_name}'.")
                return

            # Read the content of routes.py
            with open(routes_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace 'package_name.package_name' with 'package_name'
            content = content.replace(f'{package_name}.{package_name}', package_name)

            # Ensure the output directory exists
            os.makedirs(output_directory, exist_ok=True)

            # Write the modified content to a new file in the output directory
            if output_filepath is None:
                output_filepath = os.path.join(output_directory, f'{package_name}_route.py')

            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Extracted routes.py from package '{package_name}' to '{output_filepath}'.")
        except ImportError:
            print(f"Package '{package_name}' not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
