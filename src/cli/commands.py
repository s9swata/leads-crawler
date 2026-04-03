"""CLI commands for lead-gen."""

import click


@click.command(name="search")
@click.option("--query", required=True, help="Search query for finding leads")
@click.option("--location", help="Location to search in")
@click.option("--limit", default=10, help="Maximum number of results")
def search(query, location, limit):
    """Search for business leads based on query and location."""
    click.echo(f"Searching for: {query}")
    if location:
        click.echo(f"Location: {location}")
    click.echo(f"Limit: {limit}")


@click.command(name="scrape")
@click.option("--url", required=True, help="URL to scrape")
@click.option("--output", help="Output file path")
def scrape(url, output):
    """Scrape contact information from a URL."""
    click.echo(f"Scraping: {url}")
    if output:
        click.echo(f"Output: {output}")


@click.command(name="init")
def init():
    """Initialize a new lead generation project with default config."""
    click.echo("Initializing lead-gen project...")
    click.echo("Creating default config file...")


@click.command(name="export")
@click.option(
    "--format", type=click.Choice(["csv", "json"]), default="csv", help="Export format"
)
@click.option("--columns", help="Comma-separated list of columns to export")
def export_cmd(format, columns):
    """Export leads to CSV or JSON format."""
    click.echo(f"Exporting in format: {format}")
    if columns:
        click.echo(f"Columns: {columns}")
