"""CLI commands for lead-gen."""

import asyncio
import json

import click

from src.extraction.adapters import Crawl4aiAdapter
from src.extraction.extractors import (
    EmailExtractor,
    PhoneExtractor,
    SocialExtractor,
    WebsiteExtractor,
)
from src.core.rate_limiter import RateLimiter
from src.core.robots import RobotsTxtParser
from src.config.settings import Settings


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
@click.option(
    "--format",
    type=click.Choice(["json", "text"]),
    default="json",
    help="Output format",
)
def scrape(url, format):
    """Scrape contact information from a URL."""
    asyncio.run(_scrape(url, format))


async def _scrape(url: str, output_format: str):
    """Execute scrape asynchronously."""
    settings = Settings()
    rate_limiter = RateLimiter(settings)
    robots_parser = RobotsTxtParser(settings)

    from crawl4ai import AsyncWebCrawler

    crawler = AsyncWebCrawler()
    await crawler.start()

    adapter = Crawl4aiAdapter(
        crawler=crawler,
        rate_limiter=rate_limiter,
        robots_parser=robots_parser,
    )

    try:
        html = await adapter.fetch_if_allowed(url)

        email_extractor = EmailExtractor()
        phone_extractor = PhoneExtractor()
        social_extractor = SocialExtractor()
        website_extractor = WebsiteExtractor()

        emails = email_extractor.extract_from_html(html)
        phones = phone_extractor.extract_from_html(html)
        social = social_extractor.extract_from_html(html)
        websites = website_extractor.extract_from_html(html, base_url=url)

        result = {
            "url": url,
            "emails": emails,
            "phones": phones,
            "social": social,
            "websites": websites,
        }

        if output_format == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            if emails:
                click.echo("Emails: " + ", ".join(emails))
            if phones:
                click.echo("Phones: " + ", ".join(phones))
            if social:
                click.echo("Social: " + ", ".join(social))
            if websites:
                click.echo("Websites: " + ", ".join(websites))
    finally:
        await crawler.close()


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
