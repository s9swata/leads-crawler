"""Lead Generation CLI - Find and extract business contact information."""

import click
from src.cli.commands import search, scrape, init, export_cmd, leads
from src.config.settings import Settings


@click.group()
@click.version_option(version="0.1.0")
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to configuration file (YAML or JSON)",
)
@click.pass_context
def cli(ctx, config):
    """Lead Generation CLI - Find and extract business contact information."""
    ctx.ensure_object(dict)
    if config:
        ctx.obj["settings"] = Settings.from_path(config)
    else:
        ctx.obj["settings"] = Settings()


cli.add_command(search)
cli.add_command(scrape)
cli.add_command(init)
cli.add_command(leads)
cli.add_command(export_cmd)


if __name__ == "__main__":
    cli()
