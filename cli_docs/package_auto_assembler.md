
``` bash
paa --help
```

```
Usage: paa [OPTIONS] COMMAND [ARGS]...

  Package Auto Assembler CLI tool.

Options:
  --help  Show this message and exit.

Commands:
  check-vulnerabilities  Check vulnerabilities of the module.
  init-config            Initialize config file
  make-package           Package with package-auto-assembler.
  test-install           Test install module into local environment.
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

Installing packages for a test in local environemnts could be a useful step to make sure everything works as expected before pushing changes to publishing repo. This creates an instance of the package in local environment with default version, with a greatly simplified building process that avoids making documentationm, versioning and so on.

``` bash
paa test-install [OPTIONS] MODULE_NAME
```

```
Usage: paa test-install [OPTIONS] MODULE_NAME

  Test install module for .py file in local environment

Options:
  --config TEXT                Path to config file for paa.
  --module-filepath TEXT       Path to .py file to be packaged.
  --mapping-filepath TEXT      Path to .json file that maps import to install
                               dependecy names.
  --cli-module-filepath TEXT   Path to .py file that contains cli logic.
  --dependencies-dir TEXT      Path to directory with local dependencies of
                               the module.
  --default-version TEXT       Default version.
  --check-vulnerabilities      If checked, checks module dependencies with
                               pip-audit for vulnerabilities.
  --keep-temp-files            If checked, setup directory won't be removed
                               after setup is done.
  --help                       Show this message and exit.
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