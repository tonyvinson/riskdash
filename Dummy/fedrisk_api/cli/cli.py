import logging
import os

import click

from fedrisk_api.__init__ import __version__

CMD_FOLDER = os.path.join(os.path.dirname(__file__), "commands")
CMD_PREFIX = "cmd_"

LOGGER = logging.getLogger(__name__)


class CLI(click.MultiCommand):
    """Main Command Class."""

    def list_commands(self, ctx):
        """Obtain a list of all available commands.

        Args:
            ctx (dictionary): Click context object

        Returns:
            list: a list of sorted commands
        """

        commands = []

        for filename in os.listdir(CMD_FOLDER):
            if filename.endswith(".py") and filename.startswith(CMD_PREFIX):
                commands.append(filename[4:-3])

        return commands

    def get_command(self, ctx, name):  # pylint: disable=arguments-differ
        """Get a specific command by looking up the module.

        Args:
            ctx (dictionary): Click context object
            name (string): Command name

        Returns:
            function: Module's cli function
        """

        namespace = {}

        filename = os.path.join(CMD_FOLDER, CMD_PREFIX + name + ".py")

        try:
            with open(filename) as opened_file:
                code = compile(opened_file.read(), filename, "exec")  # noqa: WPS421
                eval(  # nosec  # noqa  # pylint: disable=eval-used
                    code,
                    namespace,
                    namespace,
                )

            return namespace["cli"]
        except OSError as ignore:  # pylint: disable=W0612  # noqa
            return None


@click.command(cls=CLI, name="fedrisk_api")
@click.version_option(__version__)
@click.option("-d", "--debug", is_flag=True, help="turn debug logging on")
@click.option("--nocolor", is_flag=True, help="turn OFF colorized logging")
@click.option("--dark_theme", is_flag=True, help="use color scheme for Dark console")
def cli(debug=False, nocolor=False, dark_theme=False):
    """Fedrisk_api  Command Line Tool.

    Args:
        debug (bool): Set this to True to turn on Debug
        nocolor (bool): Set this to True to turn off Colorized Logging
        dark_theme (bool): Set this to True to use Dark Theme Colors

    """

    ctx = click.get_current_context()
    ctx.obj = {}

    # Set up Colorized Logging
    use_color = not nocolor
    use_light_theme = not dark_theme

    log_level = logging.DEBUG if debug else logging.INFO


if __name__ == "__main__":
    cli()  # pylint: disable=E1120

# End of WPG controlled content - anything after this line will be maintained
