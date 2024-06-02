import click
from example_module.example_module import greet, farewell  # Import your functions

@click.group()
def cli():
    """Example CLI tool with multiple commands."""
    pass

@click.command()
@click.argument('name')
@click.option('--greet', 'greet_option', is_flag=True, help='Include to greet the user')
@click.option('--age', type=int, help='Your age')
@click.option('--city', type=str, help='Your city')
@click.option('--verbose', is_flag=True, help='Enable verbose mode')
def hello(name, greet_option, age, city, verbose):
    """Say hello to the user."""
    if verbose:
        click.echo(f"Verbose mode enabled")

    if greet_option:
        result = greet(name=name, age=age)
        click.echo(result)
    else:
        click.echo(name)

@click.command()
@click.argument('name')
@click.option('--farewell', 'farewell_option', is_flag=True, help='Include to say farewell to the user')
def goodbye(name, farewell_option):
    """Say goodbye to the user."""
    if farewell_option:
        click.echo(farewell(name))
    else:
        click.echo(f"{name}")

cli.add_command(hello)
cli.add_command(goodbye)

if __name__ == "__main__":
    cli()
