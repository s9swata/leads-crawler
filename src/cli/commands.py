"""CLI commands for lead-gen."""

import asyncio
import json
from typing import Optional

import click
from tqdm import tqdm

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
from src.storage.database import session_scope
from src.storage.query_builder import build_leads_query
from src.export.csv_generator import export_csv
from src.export.columns import AVAILABLE_COLUMNS
from src.storage.lead_ingestion import LeadIngestionService


@click.command(name="search")
@click.option("--query", required=True, help="Search query for finding leads")
@click.option("--location", help="Location to search in")
@click.option("--limit", default=10, help="Maximum number of results")
@click.option(
    "--ingest/--no-ingest",
    default=False,
    help="Ingest results to database for later scraping",
)
def search(query, location, limit, ingest):
    """Search for business leads based on query and location."""
    settings = Settings()
    if not settings.serper_api_key:
        raise click.ClickException(
            "SERPER_API_KEY not set. Get one at https://serper.dev/ and set it in your .env file."
        )

    asyncio.run(_search(query, location, limit, ingest, settings))


async def _search(query: str, location: str, limit: int, ingest: bool, settings):
    from src.search.adapters import SerperAdapter

    adapter = SerperAdapter(settings.serper_api_key)

    if location:
        full_query = f"{query} {location}"
    else:
        full_query = query

    click.echo(f"Searching for: {full_query}")

    try:
        # Show progress bar during search
        with tqdm(total=limit, desc="Searching", unit="results", leave=True) as pbar:
            results = await adapter.search(full_query, limit)
            pbar.update(len(results))
    except Exception as e:
        raise click.ClickException(f"Search failed: {e}")

    if not results:
        click.echo("No results found.")
        return

    click.echo(f"\nFound {len(results)} results:\n")

    ingestion_service = LeadIngestionService()
    ingested_count = 0

    for i, result in enumerate(results, 1):
        click.echo(f"{i}. {result.title}")
        click.echo(f"   URL: {result.url}")
        click.echo(f"   Snippet: {result.snippet[:100]}...")
        click.echo()

        if ingest:
            added, duplicates, _ = ingestion_service.ingest(
                data={"url": result.url, "company_name": result.title},
                source="search",
                source_url=result.url,
            )
            if added:
                ingested_count += 1

    if ingest:
        click.echo(f"Ingested {ingested_count} leads to database.")


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

        ingestion_service = LeadIngestionService()
        added, duplicates, leads = ingestion_service.ingest(
            data=result,
            source="scrape",
            source_url=url,
        )

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

        click.echo(f"Stored {added} new leads, {duplicates} duplicates skipped")
    finally:
        await crawler.close()


@click.command(name="init")
def init():
    """Initialize a new lead generation project with default config."""
    click.echo("Initializing lead-gen project...")
    click.echo("Creating default config file...")


@click.command(name="leads")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option("--per-page", "-n", default=20, help="Items per page (default: 20)")
@click.option(
    "--filter-email/--no-email", default=None, help="Filter by email presence"
)
@click.option(
    "--filter-phone/--no-phone", default=None, help="Filter by phone presence"
)
@click.option(
    "--filter-website/--no-website", default=None, help="Filter by website presence"
)
@click.option("--source", help="Filter by source (search, scrape, manual)")
@click.option(
    "--sort",
    type=click.Choice(["discovered_at", "source", "company_name", "scraped_at"]),
    default="discovered_at",
    help="Sort field",
)
@click.option(
    "--order", type=click.Choice(["asc", "desc"]), default="desc", help="Sort order"
)
def leads(
    page, per_page, filter_email, filter_phone, filter_website, source, sort, order
):
    """View leads with filtering, sorting, and pagination."""
    from src.storage.lead_repo import LeadRepository

    with session_scope() as session:
        repo = LeadRepository(session)

        offset = (page - 1) * per_page
        leads_list = build_leads_query(
            session,
            has_email=filter_email,
            has_phone=filter_phone,
            has_website=filter_website,
            source=source,
            sort_by=sort,
            sort_order=order,
            limit=per_page,
            offset=offset,
        )

        if not leads_list:
            click.echo("No leads found.")
            return

        for lead in leads_list:
            click.echo(f"\n--- Lead: {lead.company_name} ---")
            click.echo(f"  Source: {lead.source}")
            if lead.email:
                click.echo(f"  Email: {lead.email}")
            if lead.website:
                click.echo(f"  Website: {lead.website}")
            if lead.phone:
                click.echo(f"  Phone: {lead.phone}")
            if lead.linkedin:
                click.echo(f"  LinkedIn: {lead.linkedin}")
            click.echo(f"  Discovered: {lead.discovered_at}")

        total = repo.count()
        total_pages = (total + per_page - 1) // per_page
        click.echo(f"\n--- Page {page}/{total_pages} | Total: {total} leads ---")


@click.command(name="export")
@click.option("--output", "-o", required=True, help="Output CSV file path")
@click.option("--columns", help="Comma-separated list of columns to export")
@click.option(
    "--filter-email/--no-email", default=None, help="Filter by email presence"
)
@click.option(
    "--filter-phone/--no-phone", default=None, help="Filter by phone presence"
)
@click.option(
    "--filter-website/--no-website", default=None, help="Filter by website presence"
)
@click.option("--source", help="Filter by source (search, scrape, manual)")
def export_cmd(output, columns, filter_email, filter_phone, filter_website, source):
    """Export leads to CSV format."""
    column_list = None
    if columns:
        column_list = [col.strip() for col in columns.split(",")]

    with session_scope() as session:
        leads_list = build_leads_query(
            session,
            has_email=filter_email,
            has_phone=filter_phone,
            has_website=filter_website,
            source=source,
            sort_by="discovered_at",
            sort_order="desc",
            limit=10000,
            offset=0,
        )

        if not leads_list:
            click.echo("No leads to export.")
            return

        count = export_csv(leads_list, output, column_list)
        click.echo(f"Exported {count} leads to {output}")
