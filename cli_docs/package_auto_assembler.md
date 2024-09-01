
``` bash
paa --help
```

```
Usage: paa [OPTIONS] COMMAND [ARGS]...

  Package Auto Assembler CLI tool.

Options:
  --help  Show this message and exit.

Commands:
  check-vulnerabilities     Check vulnerabilities of the module.
  init-config               Initialize config file
  make-package              Package with package-auto-assembler.
  show-module-info          Shows module info.
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
  --skip-deps-install         If checked, existing dependencies from env will
                              be reused.
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

```
Usage: paa show-module-info [OPTIONS] LABEL_NAME

  Shows module info.

Options:
  --is-cli        If checked, returns true when cli interface is available.
  --keywords      If checked, returns keywords for the package.
  --classifiers   If checked, returns classfiers for the package.
  --docstring     If checked, returns docstring of the package.
  --author        If checked, returns author of the package.
  --author-email  If checked, returns author email of the package.
  --version       If checked, returns installed version of the package.
  --pip-version   If checked, returns pip latest version of the package.
  --paa-version   If checked, returns packaging tool version with which the
                  package was packaged.
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