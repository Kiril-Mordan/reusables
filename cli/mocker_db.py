import os
import shutil
import yaml
import click #==8.1.3
from uvicorn import run as uvicorn_run #==0.29.0
import fastapi #==0.109.1
from git import Repo #==3.1.41
from mocker_db.mocker_db import MockerDB
import appdirs #==1.4.3

__cli_metadata__ = {
    "name": "mockerdb"
}

def get_cache_dir():
    """
    Gets the cache directory for the application
    """

    cache_dir = appdirs.user_cache_dir(__cli_metadata__["name"])
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir

def read_and_edit_yaml(file_path, edits):
    """
    Reads a YAML file, returns its original content and updates it based on the provided dictionary.

    :param file_path: str, path to the YAML file.
    :param edits: dict, dictionary containing the key-value pairs to be edited.
    :return: tuple, original and updated content of the YAML file.
    """
    # Read the YAML file
    with open(file_path, 'r') as file:
        original_content = yaml.safe_load(file)

    # Make a copy of the original content to edit
    updated_content = original_content.copy()

    # Edit the YAML content based on the provided dictionary
    updated_content.update(edits)

    # Write the updated content back to the YAML file
    with open(file_path, 'w') as file:
        yaml.safe_dump(updated_content, file)

    return original_content, updated_content

def ensure_directory_exists(directory_path):
    """
    Checks if the specified directory path exists, and if not, creates an empty directory.

    :param directory_path: str, path to the directory.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.")

@click.group()
def cli():
    """Mocker-db CLI tool"""
    pass

@cli.command()
@click.option('--persist-path', 'persist_path', default=None, help='Path where cache data will be saved. Path will be cached.')
@click.option('--repo-url', default="https://github.com/Kiril-Mordan/MockerDB.git", help='The URL of the GitHub repository to clone.')
@click.option('--host', default='127.0.0.1', help='The host to bind to.')
@click.option('--port', default=8000, help='The port to bind to.')
@click.option('--reload', is_flag=True, help='Enable auto-reload.')
@click.option('--dump-cache', 'dump_cache', is_flag=True, help='Overwrites existing cache.')

def runserver(persist_path, repo_url, host, port, reload, dump_cache):
    """Run the FastAPI server for MockerDB."""
    cache_dir = get_cache_dir()
    click.echo(f"Using cache directory: {cache_dir}")

    repo_dir = os.path.join(cache_dir, "repo")

    if dump_cache and os.path.exists(repo_dir):
        click.echo(f"Refreshing cache: deleting contents of {repo_dir}")
        shutil.rmtree(repo_dir)

    if os.path.exists(repo_dir):
        click.echo(f"Using existing repository in {repo_dir}")
    else:
        click.echo(f"Cloning repository to {repo_dir}")
        Repo.clone_from(repo_url, repo_dir)

    app_file = 'main.py'  # Assuming 'main.py' is the entry point of the FastAPI app
    app_path = os.path.join(repo_dir, app_file)
    if not os.path.exists(app_path):
        click.echo(f"Error: {app_file} not found in the repository {repo_url}")
        return

    click.echo(f"Starting FastAPI server from {app_path}")
    # Change the working directory to the repo_dir
    os.chdir(repo_dir)

    # If persist path provided, save cache there
    if persist_path:

        if os.path.isdir(persist_path):
            ensure_directory_exists(persist_path)

        yaml_file_path = './conf/mocker_setup_params.yaml'
        edits_to_make = {
            'file_path' : os.path.join(persist_path, "mock_persist"),
            'embs_file_path' : os.path.join(persist_path, "mock_embs_persist")
            }
        original_content, _ = read_and_edit_yaml(yaml_file_path, edits_to_make)

    # Ensure the directory is in the PYTHONPATH
    os.environ['PYTHONPATH'] = repo_dir

    uvicorn_run("main:app", app_dir=repo_dir, host=host, port=port, reload=reload)

cli.add_command(runserver)

if __name__ == "__main__":
    cli()
