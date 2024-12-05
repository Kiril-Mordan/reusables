## About

A Python Packaging Repository (PPR) is a Git repository with a CI/CD pipeline designed to create and publish Python packages from code pushed to the repository. Using the `package-auto-assembler` tool, PPR can dynamically generate a packaging structure for `.py` files in a highly automated manner. This allows you to publish and maintain multiple packages from a single repository.

In its simplest form, adding a new `.py` file (or modifying an existing one) triggers the CI/CD pipeline to automatically prepare and publish release of new or existing package. Packages can be published to [PyPI](https://pypi.org/) or private storage solutions such as [Azure Artifacts Storage](https://learn.microsoft.com/en-us/azure/devops/artifacts/start-using-azure-artifacts?view=azure-devops).

![publishing-repo-flow](package_auto_assembler-usage.png)

*Diagram: Automated flow for packaging and publishing Python packages using PPR.*

### Inputs and Outputs of PPR

PPR produces Python packages with the structure shown below when all optional files are present. You can find more details about these files [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#7-assembling-setup-directory).

Each package can include optional features:

- [Store files](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#13-adding-artifacts-to-packages) - Include files or links to files within the package.
- [CLI interface](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#10-adding-cli-interfaces) - Add command-line utilities to the package.
- [FastAPI routes](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#11-adding-routes-and-running-fastapi-application) - Embed API routes to run FastAPI applications from packages.
- [Streamlit apps](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#12-adding-ui-and-running-streamlit-application) - Include interactive UIs.
- [MkDocs pages](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#16-making-simple-mkdocs-site) - Generate simple static documentation websites for each package.

![Publishing Repo Input/Output](package_auto_assembler-input_output_files.png)

*Diagram: The structure includes core package files and additional optional components such as CLI interfaces, FastAPI routes, or documentation.*


## Basic usage

### 1. Prepare Local Environment

Before developing code within a packaging repository, ensure that the `package-auto-assembler` python package is installed in your environment:

``` bash
pip install package-auto-assembler
```

**Note**: Some config files, like `.pipirc` and `.pip.conf`, might be required to [configure access to private packages from Azure Artifacts storage](https://learn.microsoft.com/en-us/azure/devops/artifacts/quickstarts/python-packages?view=azure-devops&tabs=Windows#connect-to-your-feed). 

### 2. Add or Edit a Package

To prepare your code for packaging:

1. Create/find a `.py` file in `module_dir` with a name of the package (use underscores (`_`) instead of hyphens (`-`) and spaces)

2. Make sure the module you're trying to create/edit follows basic requirements, described [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#1-preparing-code-for-packaging)

3. Add/edit [optional files](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#3-preparing-files-for-packaging) and [additional documentation](https://kiril-mordan.github.io/reusables/package_auto_assembler/description/#2-preparing-documentation-for-packaging). 


**Note**: Relevant names of the directories, like `module_dir`, could be checked in `.paa.config` file from your instance of a packaging repository. This and the following steps assume that an instance of a packaging repository was already created or pulled. If not, to setup a new ppr take a look [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/python_packaging_repo/#setting-up-new-ppr). 

### 3. Test-Install a Package

After adding or editing files related to your package, install it locally and ensure it works as expected.

``` bash
paa test-install your-package
```

**Note**: Use the `--skip-deps-install` flag if reinstalling dependencies is unnecessary. More flags could be seen [here](https://kiril-mordan.github.io/reusables/package_auto_assembler/cli_tools/#creating-packages).

### 4. Push Changes to PPR

When code is ready for release, commit changes, including the package name and a list of changes in your commit messages. Push the changes to a new branch your packaging repository, then create a pull request to the `main` branch.

``` bash
git commit -m "[your_package] change one; comment about change two"
```

**Note**: Merge files for only one package at a time. The pipeline relies on commit history to determine which package to test and publish.

### 5. Publish a Package

If the test results are satisfactory, merge the pull request with `main`. The pipeline will then:

1. Initialize the packaging process.
2. Prepare the package.
3. Publish it to package storage.
4. Update tracking files in `.paa` and README.

**Note** Due to possibility of multiple packaging feeds, trigger for `azure devops + azure artifacts feed` template would not be automatic on merge, but would need to be triggered manually after merging with `main`. To do so, in your Azure DevOps project, navigate to `Pipelines` -> `your-packaging-repo-pipeline` -> `Run pipeline` and select one of the configured upload feeds in `Upload Feed` as well as indicate package to be published (ensure to use underscores (`_`) instead of hyphens (`-`)) in `Package Name` field. 

### Additional Information

To see more CLI tools and options, run:

``` bash
paa --help
```

Or visit [`package-auto-assembler` documentation](https://kiril-mordan.github.io/reusables/package_auto_assembler/).

---

## Setting up new PPR

A Python Packaging Repository can be created for:

- [GitHub](https://github.com/) with PyPI
- [Azure DevOps](https://azure.microsoft.com/en-us/products/devops) with Azure Artifacts

### Prerequisites

- **New Git Repository:** A repository where the PPR will be set up.
- **Pipeline Permissions:** CI/CD pipelines must have read and write access to commit to the repository.
- **Package Storage:**
    - **GitHub:** A [PyPI](https://pypi.org/) account.
    - **Azure DevOps:** An [Azure Artifacts Feed](https://learn.microsoft.com/en-us/azure/devops/artifacts/concepts/feeds?view=azure-devops).

Only two templates are provided:
- `github + pypi`
- `azure devops + azure artifacts feed`

### Github

1. **Set Up GitHub Pages**:
    - Navigate to `Settings` -> `Pages`.
    - Select `Deploy from a branch` choose the `gh-pages` branch (if it does not exist, create a new branch named `gh-pages`), and set the directory to `/root`. [More details](https://docs.github.com/en/pages/quickstart).

2. **Configure GitHub Actions**:
    - Navigate to `Settings` -> `Actions` -> `General`.
    - Under `Actions permissions` select `Allow all actions and reusable workflows`
    - Under `Workflow permissions` select `Read and write permissions` [More details](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

3. **Add PyPI Credentials**:
    - Go to `Settings` -> `Secrets and variables` -> `Actions`.
    - Add `TWINE_USERNAME` and `TWINE_PASSWORD` as secrets. [More details](https://pypi.org/help/#apitoken).

4. **Initialize the Template**:
    - Use `paa` to set up the PPR:
     
    ```
    paa init-ppr --github
    ```
     
    Or include all optional directories:

    ```
    paa init-ppr --github --full
    ```

    - Edit `.paa.config` if needed
    - Run `paa init-ppr --github` or `paa init-paa` a second time to initialize directories for storing packaging files based on `.paa.config`.

5. **Customize**:
    - Edit `.github/docs/README_base.md` and `.github/tools/update_README.sh` to modify the repository-level README.

Once setup is complete, pushing changes to the `main` will automatically trigger the pipeline to package and publish your Python packages.

### Azure DevOps


1. **Repository Permissions**:
    - Navigate to `Project settings` -> `Repositories` -> `Your Repository`.
    - Set `Contribute` and `Create tag` permissions for `Your project build service` to "Allow"

2. **Set Up Azure Artifacts Feed**:
    - Create an artifacts feed or use an existing one. [More details](https://learn.microsoft.com/en-us/azure/devops/artifacts/quickstarts/python-packages?view=azure-devops&tabs=Windows).


3. **Add Credentials**:
    - Generate a Personal Access Token (`TWINE_USERNAME` and `TWINE_PASSWORD`) with `Read & write`e permissions for `Packaging` [More details](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops).


4. **Initialize the Template**:

    - Use `paa` to set up the PPR:

    ```
    paa init-ppr --azure
    ```

    Or include all optional directories:

    ```
    paa init-ppr --azure --full
    ```

    - Edit `.paa.config` if needed
    - Run `paa init-ppr --azure` or `paa init-paa` a second time to initialize  directories for storing packaging files based on `.paa.config`.
    - Create `.azure/feeds/YOUR_FEED_NAME.yml` files based on `.azure/feeds/example_feed.yml` and remove the example.

5. **Configure the Pipeline**:

    - Navigate to `Pipelines` -> `New pipeline`.
    - Choose `Azure Repos Git` -> `Your Repository`.
    - Select the `main` branch and `.azure/azure-pipelines.yml` to define the pipeline configuration for packaging and publishing.
    - Add `TWINE_USERNAME` and `TWINE_PASSWORD` under "Variables"

6. **Customize**:

    - Edit `.azure/docs/README_base.md` and `.azure/tools/update_README.sh` to modify the repository-level README.

**Note:** Pushing changes to the `main` branch does not necessarily mean that a package will be published. Since multiple feeds can be published from this repository, a **manual trigger** is preferred.

To trigger the workflow:

1. Navigate to `Pipelines` -> `your-packaging-repo-pipeline` -> `Run pipeline`.
2. Select one of the configured upload feeds in the `Upload Feed` dropdown.
3. Specify the package name in the `Package Name` field (use underscores (`_`) instead of hyphens (`-`)).

---

