import click


@click.command(help="Say hello")
@click.argument("name")
def say_hello(name):
    """Say Hello to NAME.

    Args:
        name (string): Name of the person to say hello to.
    """
    click.secho(f"Hello {name}!!")


@click.group(name="hello")
def cli():
    """Hello Commands."""


cli.add_command(say_hello)
