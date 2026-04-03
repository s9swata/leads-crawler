"""Lead Generation CLI - Find and extract business contact information."""

import click
from src.cli.commands import search, scrape, init, export_cmd


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Lead Generation CLI - Find and extract business contact information."""
    pass


cli.add_command(search)
cli.add_command(scrape)
cli.add_command(init)
cli.add_command(export_cmd)


if __name__ == "__main__":
    cli()
