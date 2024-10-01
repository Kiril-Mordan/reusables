import os
import click #==8.1.7
import yaml


__cli_metadata__ = {
    "name" : "mockerdb"
}


@click.group()
@click.pass_context
def cli(ctx):
    """Package Auto Assembler CLI tool."""
    ctx.ensure_object(dict)

api_config = {
        'MOCKER_SETUP_PARAMS' : {
    'embedder_params' :
  {'model_name_or_path' : 'intfloat/multilingual-e5-base',
  'processing_type' : 'batch',
  'tbatch_size' : 500},
    'similarity_params' : {'space':'cosine'},
    'file_path' : "./persist/",
    'embs_file_path' : "./persist/",
    'similarity_search_type' : 'linear_torch',
    'persist' : True
},
'API_SETUP_PARAMS' : {
    'memory_scaler_from_bytes': 1048576,
    'allocated_mb': 8192
}
    }

@click.command()
@click.pass_context
def init_config(ctx):
    """Initialize config file for api"""

    config = ".mockerdb.api.config"

    if not os.path.exists(config):
        with open(config, 'w', encoding='utf-8') as file:
            yaml.dump(api_config, file, sort_keys=False)

        click.echo(f"Config file {config} initialized!")
        click.echo(f"Edit it to your preferance.")
    else:
        click.echo(f"Config file already exists in {config}!")


cli.add_command(init_config, "init-config")


if __name__ == "__main__":
    cli()

