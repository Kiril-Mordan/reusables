## About

Python packaging repository (PPR) is a git repository with a ci/cd pipeline, which main purpose is to create and publish python packages from the code pushed to that repo. The unique way `package-auto-assembler` is able to create packaging structure for a `.py` file dynamically, in a highly automated manner, allows to create PPR, that would allow to publish and maintain multiple packages from the same repository. 

In its simplest form, just adding a new `.py` file or adding a new one to a specific directory, would trigger a special ci/cd pipeline that would prepare and publish a release of new or existing package to [PyPi](https://pypi.org/) or some private package storages like a specific feed in [Azure Artifacts Storage](https://learn.microsoft.com/en-us/azure/devops/artifacts/start-using-azure-artifacts?view=azure-devops&tabs=nuget%2Cnugetserver%2Cnugetserver19).

![publishing-repo](package_auto_assembler-usage.png)

### Inputs and outputs of PPR

![publishing-repo](package_auto_assembler-input_output_files.png)


## Setting up new PPR

Packaging repository for both [Github](https://github.com/) and [Azure DevOps](https://azure.microsoft.com/en-us/products/devops) requires the following things:

- new repository
- read and write permissions for ci/cd pipeline to commit to your repository
- package storage either in a form of [pypi](https://pypi.org/) account (github ppr) or [azure artifacts feed](https://learn.microsoft.com/en-us/azure/devops/artifacts/concepts/feeds?view=azure-devops) (azure devops ppr)

Only two templates are provided : `github + pypi` and `azure devops + azure artifacts feed`. 

### Github

Provided PPR template also takes advantage of [Github Pages](https://pages.github.com/) to publish mkdocs static pages. 

To setup Github Pages for your new repository go to `your new repository` -> `Settings` -> `Pages`, then make sure that `Deploy from a branch` is selected and select `gh-pages` branch (create if does not exist) with `/root`. More about setting up Github Pages can be found [here](https://docs.github.com/en/pages/quickstart).

To setup ci/cd pipeline go to `your new repository` -> `Settings` -> `Actions` -> `General` and under `Actions permissions` select `Allow all actions and reusable workflows`, under `Workflow permissions` select `Read and write permissions`. More about setting up Github Actions can be found [here](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

After acquiring credentials from pypi, you should provide `TWINE_USERNAME` and `TWINE_PASSWORD` env variables for the ci/cd pipeline to publish to pypi. To do so, go to `your new repository` -> `Settings` -> `Secrets and variables` -> `Actions`  and add these variables via `New repository secret` button. More about acquiring pypi credentials for packages can be found [here](https://pypi.org/help/#apitoken).

Once all of the above is done, pushing PPR to main branch of `your new repository` can be done with a template.

To get access to the templete, run `paa init-ppr --github` or `paa init-ppr --github --full` to add all of the directories for optional files to `.paa.config`. After first run empty directories will not appear, only after running `paa init-ppr --github` or `paa init-paa` second time they appear based on `.paa.config` file. 

Additional steps may include editing `.github/docs/README_base.md` and `.github/tools/update_README.sh` to change how repository level README is constructed. 

### Azure DevOps

Creating PPR within a repository in Azure Devops requires some additional configuration within a
the project that it is located in. Assuming that project exists and one has enough permissions to change appropriate settions, go to `your project` -> `Project settings` -> `Repositories` -> `your new repository` -> `Project settings` -> `Your project build service` and set `Contribute` and `Create tag` to `Allow`.

Azure artifacts feed or feeds are needed for this template to store python packages and install packages from, [here](https://learn.microsoft.com/en-us/azure/devops/artifacts/quickstarts/python-packages?view=azure-devops&tabs=Windows) is more info on how to setup a new feed.

Credentials to be able to publish in configured azure artifacts feeds, could be aquired by going to `User settings` -> `Personal Access Tokens` -> `+ New Token` and setting up a new token that has at least `Read & write` permissions for `Packaging`. Name of token would become the value of `TWINE_USERNAME` and token itself `TWINE_PASSWORD`.

Once that's done, there are few more steps left, but first a template would need to be prepared and pushed to `main` branch of `your new repository`. 

To get access to the templete, run `paa init-ppr --azure` or `paa init-ppr --azure --full` to add all of the directories for optional files to `.paa.config`. After first run empty directories will not appear, only after running `paa init-ppr --azure` or `paa init-paa` second time they appear based on `.paa.config` file. Then go to `Artifacts` -> `your feed` -> `Connect to Feed` -> `twine`. This would show you instructions for uploading to the feed, some information from there would need to be copied to `.azure/feeds/YOUR_FEED.yml`. In the `.azure/feeds/example_feed.yml` is an example of how this would look like. More feeds could be added by adding additional `.yml` files (feed would then be selected when running the pipeline). When that's done, push to `main` branch of `your new repository`.

Since the pipeline is likely not be recognized automatically, the next step would be to go to `Pipelines` -> `New pipeline` -> `Azure Repos Git` -> `your new repository` -> `Existing Azure Pipelines YAML file`, then make sure `main` branch is selected and select `.azure/azure-pipelines.yml` in path. After that select `Variables` and add `TWINE_USERNAME` and `TWINE_PASSWORD`. 

Additional steps may include editing `.azure/docs/README_base.md` and `.azure/tools/update_README.sh` to change how repository level README is constructed. 



