"""CowAgent CLI entry point."""

import click
from cli import __version__
from cli.commands.skill import skill
from cli.commands.process import start, stop, restart, status, logs
from cli.commands.context import context


@click.group()
@click.version_option(__version__, '--version', '-v', prog_name='cow')
def main():
    """CowAgent CLI - Manage your CowAgent instance."""
    pass


main.add_command(skill)
main.add_command(start)
main.add_command(stop)
main.add_command(restart)
main.add_command(status)
main.add_command(logs)
main.add_command(context)


if __name__ == '__main__':
    main()
