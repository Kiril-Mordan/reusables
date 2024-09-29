
``` bash
paa --help
```

```
Usage: paa [OPTIONS] COMMAND [ARGS]...

  Package Auto Assembler CLI tool.

Options:
  --help  Show this message and exit.

Commands:
  check-licenses            Check licenses of the module.
  check-vulnerabilities     Check vulnerabilities of the module.
  extract-module-artifacts  Extracts artifacts from packaged module.
  extract-module-routes     Extracts routes for fastapi from packages...
  extract-module-site       Extracts static mkdocs site from packaged...
  init-config               Initialize config file
  make-package              Package with package-auto-assembler.
  run-api-routes            Run fastapi with provided routes.
  show-module-artifacts     Shows module artifacts.
  show-module-info          Shows module info.
  show-module-licenses      Shows module licenses.
  show-module-list          Shows module list.
  show-module-requirements  Shows module requirements.
  test-install              Test install module into local environment.
  update-release-notes      Update release notes.
```

Creating config file could be useful to avoid providing parameters manually. If no config file will be provided, by default values from `.paa.config` will be used.

``` bash
paa init-config  --help
```

```
Usage: paa init-config [OPTIONS]

  Initialize config file

Options:
  --help  Show this message and exit.
```

Making package based on provided parameters can be useful in ci/cd pipelines to streamline creation of packages before publishing from something that could be as simple as `.py` file.

``` bash
paa make-package --help
```

```
Usage: paa make-package [OPTIONS] MODULE_NAME

  Package with package-auto-assembler.

Options:
  --config TEXT                   Path to config file for paa.
  --module-filepath TEXT          Path to .py file to be packaged.
  --mapping-filepath TEXT         Path to .json file that maps import to
                                  install dependecy names.
  --cli-module-filepath TEXT      Path to .py file that contains cli logic.
  --dependencies-dir TEXT         Path to directory with local dependencies of
                                  the module.
  --kernel-name TEXT              Kernel name.
  --python-version TEXT           Python version.
  --default-version TEXT          Default version.
  --ignore-vulnerabilities-check  If checked, does not check module
                                  dependencies with pip-audit for
                                  vulnerabilities.
  --example-notebook-path TEXT    Path to .ipynb file to be used as README.
  --execute-notebook              If checked, executes notebook before turning
                                  into README.
  --log-filepath TEXT             Path to logfile to record version change.
  --versions-filepath TEXT        Path to file where latest versions of the
                                  packages are recorded.
  --help                          Show this message and exit.
```

Installing packages for a test in local environments could be a useful step to make sure everything works as expected before pushing changes to publishing repo. This creates an instance of the package in local environment with default version, with a greatly simplified building process that avoids making documentation, versioning and so on.

``` bash
paa test-install [OPTIONS] MODULE_NAME
```

```
Usage: paa test-install [OPTIONS] MODULE_NAME

  Test install module into local environment.

Options:
  --config TEXT                   Path to config file for paa.
  --module-filepath TEXT          Path to .py file to be packaged.
  --mapping-filepath TEXT         Path to .json file that maps import to
                                  install dependecy names.
  --cli-module-filepath TEXT      Path to .py file that contains cli logic.
  --fastapi-routes-filepath TEXT  Path to .py file that routes for fastapi.
  --dependencies-dir TEXT         Path to directory with local dependencies of
                                  the module.
  --default-version TEXT          Default version.
  --check-vulnerabilities         If checked, checks module dependencies with
                                  pip-audit for vulnerabilities.
  --build-mkdocs                  If checked, builds mkdocs documentation.
  --check-licenses                If checked, checks module dependencies
                                  licenses.
  --keep-temp-files               If checked, setup directory won't be removed
                                  after setup is done.
  --skip-deps-install             If checked, existing dependencies from env
                                  will be reused.
  --help                          Show this message and exit.
```

Checking vulnerabilities with `pip-audit` is usefull. This checks vulnerabilities of .py files and its local dependencies with `pip-audit`.

``` bash
paa check-vulnerabilities --help
```

```
Usage: paa check-vulnerabilities [OPTIONS] MODULE_NAME

  Check vulnerabilities of the module.

Options:
  --config TEXT               Path to config file for paa.
  --module-filepath TEXT      Path to .py file to be packaged.
  --mapping-filepath TEXT     Path to .json file that maps import to install
                              dependecy names.
  --cli-module-filepath TEXT  Path to .py file that contains cli logic.
  --dependencies-dir TEXT     Path to directory with local dependencies of the
                              module.
  --help                      Show this message and exit.
```

Checking license labels of module dependencies tree could be useful to prevent using some dependencies early on.

```
Usage: paa check-licenses [OPTIONS] MODULE_NAME

  Check licenses of the module.

Options:
  --config TEXT                   Path to config file for paa.
  --module-filepath TEXT          Path to .py file to be packaged.
  --mapping-filepath TEXT         Path to .json file that maps import to
                                  install dependecy names.
  --license-mapping-filepath TEXT
                                  Path to .json file that maps license labels
                                  to install dependecy names.
  --cli-module-filepath TEXT      Path to .py file that contains cli logic.
  --dependencies-dir TEXT         Path to directory with local dependencies of
                                  the module.
  --skip-normalize-labels         If checked, package license labels are not
                                  normalized.
  --help                          Show this message and exit.
```

Maintaining release notes could be very useful, but also tedious task. 
Since commit messages are rather standard practice, by taking advantage of them and constructing release notes based on them, each release could contain notes with appropriate version automatically, when itegrated into ci/cd pipeline, given that commit messages are written in a specific way. 

``` bash
paa update-release-notes --help
```

```
Usage: paa update-release-notes [OPTIONS] LABEL_NAME

  Update release notes.

Options:
  --version TEXT           Version of new release.
  --notes TEXT             Optional manually provided notes string, where each
                           note is separated by ; and increment type is
                           provide in accordance to paa documentation.
  --notes-filepath TEXT    Path to .md wit release notes.
  --max-search-depth TEXT  Max search depth in commit history.
  --use-pip-latest         If checked, attempts to pull latest version from
                           pip.
  --help                   Show this message and exit.
```

Cli interface provides some additional tools to analyse locally installed packages if they were build with package-auto-assembler>0.4.2. These include methods to list modules, show module info, extract requirements.

``` bash
paa show-module-list --help
```

```
Usage: paa show-module-list [OPTIONS]

  Shows module list.

Options:
  --tags TEXT  Keyword tag filters for the package.
  --help       Show this message and exit.
```


``` bash
paa show-module-info --help
```

Packaging process could help building APIs as well. This package would call routes stored within other packages and routes stored in files to form one application, so that repeatable structure does not need to copied between projects, but instead built in one places and extended with some config files in many. Since routes are python code that can have its dependencies, it makes sense to store them within packages sometimes to take advantage of automated dependency handling and import code straight from the package, eliminating in turn situation when package release in no compatible anymore with routes based on them. 

Parameters for fastapi app description, middleware and run could be supplied via optional `.paa.api.config` file, with `DESCRIPTION` , `MIDDLEWARE` and `RUN` dictionary of parameters respectively. 

It could be beneficial to add a static page with documentation, so additional pages could be addded. First one would be accessible via `\mkdocs` and the following ones via `\mkdocs {i+1}`. Static package within package, that were packages by `package-auto-assemble>0.5.1` would be accessible via `\{package_name}\docs` if available.

``` bash
paa run-api-routes --help
```

```
Usage: paa run-api-routes [OPTIONS]

  Run fastapi with provided routes.

Options:
  --api-config TEXT  Path to yml config file with app description, middleware
                     parameters, run parameters, `.paa.api.config` is used by
                     default.
  --host TEXT        The host to bind to.
  --port TEXT        The port to bind to.
  --package TEXT     Package names from which routes will be added to the app.
  --route TEXT       Paths to routes which will be added to the app.
  --docs TEXT        Paths to static docs site which will be added to the app.
  --help             Show this message and exit.
```

Storing routes within package could be convinient, but extracting them from a package is not. To mitigate that, the following exists to extract `routes.py` from a package that contains it.

```
paa extract-module-routes --help
```

```
Usage: paa extract-module-routes [OPTIONS] PACKAGE_NAME

  Extracts routes for fastapi from packages that have them into a file.

Options:
  --output-dir TEXT   Directory where routes extracted from the package will
                      be copied to.
  --output-path TEXT  Filepath to which routes extracted from the package will
                      be copied to.
  --help              Show this message and exit.
```

```
Usage: paa extract-module-artifacts [OPTIONS] PACKAGE_NAME

  Extracts artifacts from packaged module.

Options:
  --artifact TEXT     Name of the artifact to be extracted.
  --output-dir TEXT   Directory where artifacts extracted from the package
                      will be copied to.
  --output-path TEXT  Filepath to which artifact extracted from the package
                      will be copied to.
  --help              Show this message and exit.
```

```
Usage: paa extract-module-site [OPTIONS] PACKAGE_NAME

  Extracts static mkdocs site from packaged module.

Options:
  --output-dir TEXT   Directory where routes extracted from the package will
                      be copied to.
  --output-path TEXT  Filepath to which routes extracted from the package will
                      be copied to.
  --help              Show this message and exit.
```

```
Usage: paa show-module-info [OPTIONS] LABEL_NAME

  Shows module info.

Options:
  --keywords      If checked, returns keywords for the package.
  --classifiers   If checked, returns classfiers for the package.
  --docstring     If checked, returns docstring of the package.
  --author        If checked, returns author of the package.
  --author-email  If checked, returns author email of the package.
  --version       If checked, returns installed version of the package.
  --pip-version   If checked, returns pip latest version of the package.
  --help          Show this message and exit.
```

``` bash
paa show-module-requirements --help
```

```
Usage: paa show-module-requirements [OPTIONS] LABEL_NAME

  Shows module requirements.

Options:
  --help  Show this message and exit.
```

``` bash
paa show-module-licenses --help
```

```
Usage: paa show-module-licenses [OPTIONS] PACKAGE_NAME

  Shows module licenses.

Options:
  --normalize-labels  If checked, package license labels are normalized.
  --help              Show this message and exit.
```

```
Usage: paa extract-module-artifacts [OPTIONS] PACKAGE_NAME

  Extracts artifacts from packaged module.

Options:
  --artifact TEXT     Name of the artifact to be extracted.
  --output-dir TEXT   Directory where artifacts extracted from the package
                      will be copied to.
  --output-path TEXT  Filepath to which artifact extracted from the package
                      will be copied to.
  --help              Show this message and exit.
```