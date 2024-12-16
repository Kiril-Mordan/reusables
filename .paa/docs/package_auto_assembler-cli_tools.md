
## About

One of available interfaces to use PAA capabalities is cli tools. After installing [`package-auto-assembler`](https://kiril-mordan.github.io/reusables/package_auto_assembler/) one can view the list of available cli tools like shown below.

``` bash
paa --help
```

``` bash
Usage: paa [OPTIONS] COMMAND [ARGS]...

  Package Auto Assembler CLI tool.

Options:
  --help  Show this message and exit.

Commands:
  check-licenses               Check licenses of the module.
  check-vulnerabilities        Check vulnerabilities of the module.
  convert-drawio-to-png        Converts drawio file to .png
  extract-module-artifacts     Extracts artifacts from packaged module.
  extract-module-requirements  Extract module requirements.
  extract-module-routes        Extracts routes for fastapi from packages...
  extract-module-site          Extracts static mkdocs site from packaged...
  extract-module-streamlit     Extracts streamlit from packages that have...
  extract-tracking-version     Get latest package version.
  init-config                  Initialize config file
  init-paa                     Initialize paa tracking files and...
  init-ppr                     Initialize ppr for a given workflows...
  make-package                 Package with package-auto-assembler.
  refresh-module-artifacts     Refreshes module artifact from links.
  remove-package               Remove paa package from ppr
  rename-package               Rename paa package in ppr
  run-api-routes               Run fastapi with provided routes.
  run-pylint-tests             Run pylint tests for a given module, file,...
  run-streamlit                Run streamlit application from the package.
  show-module-artifacts        Shows module artifacts.
  show-module-artifacts-links  Shows module artifact links.
  show-module-info             Shows module info.
  show-module-licenses         Shows module licenses.
  show-module-list             Shows module list.
  show-module-requirements     Shows module requirements.
  show-ref-local-deps          Shows paths to local dependencies...
  test-install                 Test install module into local environment.
  unfold-package               Unfold paa package inside ppr
  update-release-notes         Update release notes.
```

Available cli tools usually employ multiple internal components and range from relatively simple ones to more complex. 

![publishing-repo](package_auto_assembler-cli_capabilities.png)

## Description of tools

### Initializing PAA

Creating config file could be useful to avoid providing parameters manually. If no config file will be provided, by default values from `.paa.config` will be used.

``` bash
paa init-config  --help
```

``` bash
Usage: paa init-config [OPTIONS]

  Initialize config file

Options:
  --full  If checked, dirs beyond essential would be mapped.
  --help  Show this message and exit.
```

Packaging repository needs a place to keep some tracking files.
Running it first time also initializes `.paa.config` and the second time
will create directories specified there, if not already created.  

``` bash
paa init-paa  --help
```

``` bash
Usage: paa init-paa [OPTIONS]

  Initialize paa tracking files and directores from .paa.config

Options:
  --full  If checked, dirs beyond essential would be mapped.
  --help  Show this message and exit.
```

The package provides some templates for packaging repositories. Packaging repository after some additional preparations should allow to create and publish new packages with a use of ci/cd pipeline. 

``` bash
paa init-ppr --help
```

``` bash
Usage: paa init-ppr [OPTIONS]

  Initialize ppr for a given workflows platform.

Options:
  --github  If checked, git actions template would be set up.
  --azure   If checked, azure devops pipelines template would be set up.
  --full    If checked, dirs beyond essential would be mapped.
  --help    Show this message and exit.
```

### Creating packages

Installing packages for a test in local environments could be a useful step to make sure everything works as expected before pushing changes to publishing repo. This creates an instance of the package in local environment with default version, with a greatly simplified building process that avoids making documentation, versioning and so on.

``` bash
paa test-install [OPTIONS] MODULE_NAME
```

``` bash
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

Making package based on provided parameters can be useful in ci/cd pipelines to streamline creation of packages before publishing from something that could be as simple as `.py` file.

``` bash
paa make-package --help
```

``` bash
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

### Working with packages within PAA

Published packages could be installed and unfolded for editing anywhere, given that they are independent of a packaging repositories and enviroment that produced them.

``` bash
paa unfold-package --help
```

``` bash
Usage: paa unfold-package [OPTIONS] MODULE_NAME

  Unfold paa package inside ppr

Options:
  --debug  If checked, debug messages will be shown.
  --help   Show this message and exit.
```

Since packaging repository is just a workbench, ability to remove packages that no longer being published there could be useful. 

``` bash
paa remove-package --help
```

``` bash
Usage: paa remove-package [OPTIONS] MODULE_NAME

  Remove paa package from ppr

Options:
  --debug  If checked, debug messages will be shown.
  --help   Show this message and exit.
```

Ability to unfold packages created with `package-auto-assembler`, paired with a method to rename them, would allow to fork the package and start publishing it in the same package storage, just under different name.

``` bash
paa rename-package --help
```

``` bash
Usage: paa rename-package [OPTIONS] MODULE_NAME NEW_MODULE_NAME

  Rename paa package in ppr

Options:
  --debug  If checked, debug messages will be shown.
  --help   Show this message and exit.
```



### Checking dependencies

Checking vulnerabilities with `pip-audit` is usefull. This checks vulnerabilities of .py files and its local dependencies with `pip-audit`.

``` bash
paa check-vulnerabilities --help
```

``` bash
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

``` bash
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

### Running apps from packages

Packaging process could help building APIs as well. This package would call routes stored within other packages and routes stored in files to form one application, so that repeatable structure does not need to copied between projects, but instead built in one places and extended with some config files in many. Since routes are python code that can have its dependencies, it makes sense to store them within packages sometimes to take advantage of automated dependency handling and import code straight from the package, eliminating in turn situation when package release in no compatible anymore with routes based on them. 

Parameters for fastapi app description, middleware and run could be supplied via optional `.paa.api.config` file, with `DESCRIPTION` , `MIDDLEWARE` and `RUN` dictionary of parameters respectively. 

It could be beneficial to add a static page with documentation, so additional pages could be addded. First one would be accessible via `\mkdocs` and the following ones via `\mkdocs {i+1}`. Static package within package, that were packages by `package-auto-assemble>0.5.1` would be accessible via `\{package_name}\docs` if available.

``` bash
paa run-api-routes --help
```

``` bash
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


One of the convinient ways to access packaged code could be a streamlit application. This package allows for streamlit application to be stored within a package and then run with the following. Parameters that would be passed to `~/.streamlit/config.toml` can be provided via optional `.paa.streamlit.config` file, at which point it would copied to default location. The command can be used to run streamlit apps from a selected package, built with the tool, or from normal `.py` file with streamlit app.

``` bash
paa run-streamlit --help
```

``` bash
Usage: paa run-streamlit [OPTIONS]

  Run streamlit application from the package.

Options:
  --app-config TEXT  Path to yml config for streamlit app.
  --host TEXT        The host to bind to.
  --port TEXT        The port to bind to.
  --package TEXT     Package name from which streamlit app should be run.
  --path TEXT        Path to streamlit app.
  --help             Show this message and exit.
```

### Extracting files from packages

Storing routes within package could be convinient, but extracting them from a package is not. To mitigate that, the following exists to extract `routes.py` from a package that contains it.

``` bash
paa extract-module-routes --help
```

``` bash
Usage: paa extract-module-routes [OPTIONS] PACKAGE_NAME

  Extracts routes for fastapi from packages that have them into a file.

Options:
  --output-dir TEXT   Directory where routes extracted from the package will
                      be copied to.
  --output-path TEXT  Filepath to which routes extracted from the package will
                      be copied to.
  --help              Show this message and exit.
```

``` bash
paa extract-module-site --help
```

``` bash
Usage: paa extract-module-site [OPTIONS] PACKAGE_NAME

  Extracts static mkdocs site from packaged module.

Options:
  --output-dir TEXT   Directory where routes extracted from the package will
                      be copied to.
  --output-path TEXT  Filepath to which routes extracted from the package will
                      be copied to.
  --help              Show this message and exit.
```

Another option to access the artifacts is to copy them to a selected directory.

``` bash
paa extract-module-artifacts --help
```

``` bash
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

Another option to access the packaged streamlit app is to copy it to a selected directory.

``` bash
paa extract-module-streamlit --help
```

``` bash
Usage: paa extract-module-streamlit [OPTIONS] PACKAGE_NAME

  Extracts streamlit from packages that have them into a file.

Options:
  --output-dir TEXT   Directory where streamplit extracted from the package
                      will be copied to.
  --output-path TEXT  Filepath to which streamlit extracted from the package
                      will be copied to.
  --help              Show this message and exit.
```


### Show modules info

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

``` bash
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

``` bash
Usage: paa show-module-requirements [OPTIONS] LABEL_NAME

  Shows module requirements.

Options:
  --help  Show this message and exit.
```

``` bash
paa show-module-licenses --help
```

``` bash
Usage: paa show-module-licenses [OPTIONS] PACKAGE_NAME

  Shows module licenses.

Options:
  --normalize-labels  If checked, package license labels are normalized.
  --help              Show this message and exit.
```

There is an option to package artifacts with the code. Packaged artifacts can be listed. 

``` bash
paa show-module-artifacts --help
```

``` bash
Usage: paa show-module-artifacts [OPTIONS] LABEL_NAME

  Shows module artifacts.

Options:
  --help  Show this message and exit.
```

It might be useful to inspect which artifacts come from links, whether these links are available and refresh these artifacts within installed package.

``` bash
paa show-module-artifacts-links --help
```

``` bash
Usage: paa show-module-artifacts-links [OPTIONS] LABEL_NAME

  Shows module artifact links.

Options:
  --help  Show this message and exit.
```

A module can referance multiple other local dependencies. The following is meant to extract all of paths relates to the module within PPR.

``` bash
paa show-ref-local-deps --help
```

``` bash
Usage: paa show-ref-local-deps [OPTIONS] LABEL_NAME

  Shows paths to local dependencies referenced in the module.

Options:
  --config TEXT            Path to config file for paa.
  --module-dir TEXT        Path to folder with .py file to be packaged.
  --dependencies-dir TEXT  Path to directory with local dependencies of
                           the module.
  --help                   Show this message and exit.
```

### Other

Some artifacts can come from links and there might be a need to refresh or even download these files (depending on how a link was provided). 

``` bash
paa refresh-module-artifacts --help
```

``` bash
Usage: paa refresh-module-artifacts [OPTIONS] LABEL_NAME

  Refreshes module artifact from links.

Options:
  --help  Show this message and exit.
```

Core of paa automation is the ability to extract requirements from `.py` files. The tool shown below is a part of requirements extraction pipeline, designed to run within PPR, but could also work outside, if imports are handled in a specific way (more in description).

``` bash
paa extract-module-requirements --help
```

``` bash
Usage: paa extract-module-requirements [OPTIONS] MODULE_NAME

  Extract module requirements.

Options:
  --config TEXT                   Path to config file for paa.
  --module-dir TEXT               Path to folder where module is stored.
  --mapping-filepath TEXT         Path to .json file that maps import to
                                  install dependecy names.
  --cli-module-filepath TEXT      Path to .py file that contains cli logic.
  --routes-module-filepath TEXT   Path to .py file that contains fastapi
                                  routes.
  --streamlit-module-filepath TEXT
                                  Path to .py file that contains streamlit
                                  app.
  --dependencies-dir TEXT         Path to directory with local dependencies of
                                  the module.
  --show-extra                    If checked, list will show which
                                  requirements are extra.
  --skip-extra                    If checked, list will not include extra.
  --help                          Show this message and exit.
```


Maintaining release notes could be very useful, but also tedious task. 
Since commit messages are rather standard practice, by taking advantage of them and constructing release notes based on them, each release could contain notes with appropriate version automatically, when itegrated into ci/cd pipeline, given that commit messages are written in a specific way. 

``` bash
paa update-release-notes --help
```

``` bash
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

Running pylint tests is useful and usually done in pull request to PPR. It could also be run locally for all the modules or select modules and their local dependencies to identify modules that need improvements to pass preset threshold. 

``` bash
paa run-pylint-tests --help
```

``` bash
Usage: paa run-pylint-tests [OPTIONS] [FILES]...

  Run pylint tests for a given module, file, files or files in a directory.

Options:
  --config TEXT      Path to config file for paa.
  --label-name TEXT  Label name.
  --module-dir TEXT  Path to a directory where .py files are stored.
  --threshold TEXT   Pylint threshold.
  --help             Show this message and exit.
```

It might be useful to know what is the last version a given module that was published from the PPR, mostly within ci/cd workflows.

``` bash
paa extract-tracking-version --help
```

``` bash
Usage: paa extract-tracking-version [OPTIONS] MODULE_NAME

  Get latest package version.

Options:
  --config TEXT  Path to config file for paa.
  --help         Show this message and exit.
```

Some pieces of documentation within PPR may come from drawio files. One of the steps in packaging process is to convert `.drawio` file for a package into `.png` files. 
For this functionality to work, first some dependencies would need to be installed.

``` bash
sudo apt-get update
sudo apt-get install -y wget xvfb libnotify4 libxml2-utils
wget https://github.com/jgraph/drawio-desktop/releases/download/v24.6.4/drawio-amd64-24.6.4.deb
sudo dpkg -i drawio-amd64-24.6.4.deb
sudo apt-get install -f
```

``` bash
paa convert-drawio-to-png --help
```

``` bash
Usage: paa convert-drawio-to-png [OPTIONS]

  Converts drawio file to .png

Options:
  --config TEXT      Path to config file for paa.
  --label-name TEXT  Label name.
  --drawio-dir TEXT  Path to a directory where drawio files are stored.
  --docs-dir TEXT    Path to the output directory for .png file.
  --help             Show this message and exit.
```


