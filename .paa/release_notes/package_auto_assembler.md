# Release notes

### 0.5.16

    - default readme plus dynamic list of published packages with links to destination for github and azure templates

    - initial packaging repository setup instructions

    - azure pipelines template workflows for ppr

    - fixes for github template

    - flag to initialize all paa directories

### 0.5.15

    - github template workflows for ppr

    - init methods to setup ppr directories from template

    - additiona cli tools for pylint checks, extracting requirements and in general to handle ppr mostly from .paa.config

    - scripts to run pylint check and convert drawio to png accessible through ppr_handler

### 0.5.14

    - support for individually defined development status overwrites

    - support for extra docs from separate dir in a form of .ipynb .md .png

    - moving cli docs to new extra docs

### 0.5.13

    - initial support for streamlit app packaging

    - ability to package docs with referenced images from docs folder

    - minor fix for bug in run-api-routes that prevented usage of optional port flag

    - adding tests to packaging

    - adding drawio and unmerged .py files to tracking

### 0.5.10

    - initial cli method to extract requirements

### 0.5.9

    - support for manual overwrite for dependencies extraction

### 0.5.8

    - using module level metadata to pass links from which files are not downloaded during packaging

    - cli tools to show links and refresh artifacts from links

    - support for artifacts from links

### 0.5.7

    - fixing a problem with missing package description from jupyter

### 0.5.6

    - fixes to some problems caused by missing optional .paa.config parameters

### 0.5.5

    - minor fixes to file imports from paa artifacts

### 0.5.4

    - minor fix for packaging package without artifacts

### 0.5.3

    - additional cli tools to show and extract packaged artifacts

    - additional cli tool to extract mkdocs site

    - adding .paa tracking files to each package

    - adding optional package artifacts from a select destination in packaging repo

    - removing pypi installation instruction if pypi version is not available

    - adding all md files that start with package name to mkdocs site

### 0.5.2

    - integration of mkdocs into package building pipeline

    - packaging mkdocs static package and enabling displaying via run-module-routes functionality

    - initial ability to include docs for run-module-routes functionality

    - ability to package with artifacts

### 0.5.1

    - minor fix for requirements extraction with extra_require labels

    - fixes for the problem when __package_metadata__ is empty and .ipynb is optional

### 0.5.0

    - ability to add and run routes for fastapi applications

    - cli tools to run routes from multiple packages and filepaths

    - cli tool to extract routes from a package

    - cli and api support descriptions in docs

    - automatic extraction and processing of dependencies from api routes

### 0.4.5

    - minor fixes to license check

    - extracting extra_require labels and filtering duplicates for requirements

### 0.4.4

    - license checking integrated into packaging pipeline

    - additional cli tools to check dependencies tree and corresponding licenses

    - initial support for license labels analysis of package dependencies and their dependencies

    - initial DependenciesAnalyser for extracting info from dependencies

    - reading optional requirements from module and metadata

    - initial support for optional requirements in setup.py though extras_require

### 0.4.3

    - tagging packages with additional metadata

    - cli method to show packages in local env built with paa

    - cli method to show extended package info for packages built with paa

    - cli method to show package requirements

### 0.4.2

    - independent cli tool for updating release notes with automatic versioning

    - increasing default max search depth for commit history to 5

### 0.4.1

    - additional descriptions for each component of the package

    - fix for potential missing lines problem with setup.py creation

    - --skip-dep-install flag for test-install to reuse installed dependencies

### 0.4.0

    - getting latest version from pip and using local records as backup

    - minor fixes for version handling in release notes and empty merge history

    - support for components imports from bundles

### 0.3.1

    - release notes integragration into version interation

    - optional labels to interate version from commit messages

    - fixes for initial release notes entry

    - check-vulnerabilities with cli

### 0.2.6

    - fixes to requirements extraction from import .. as .. pattern

### 0.2.5

    - minor fixes to local dependencies with cli

### 0.2.4

    - cli handler depiction in flow diagram

    - cli name change to paa

### 0.2.3

    - initial docs for cli intefrace

    - initial  metadata extraction from cli modules to change their cli usage names from default

    - splitting package into test-install and make-package

    - adding method to initialize config

### 0.2.2

    - minor fixes for requirements extraction in preparations for cli packaging

### 0.2.1

    - initial cli interface for packaging

### 0.1.7

    - fix that skips cli packaging if cli file does not exist

### 0.1.6

    - initial cli scripts support

### 0.1.5

    - mkdocs handler to build package documentation

### 0.1.4

    - test_install_package() method for local testing

### 0.1.3

    - improved ReleaseNotesHandler with resistance to duplicate history

### 0.1.2

    - integration of pip-audit to check vulnerabilities

### 0.1.1

    - initial version with release notes handler