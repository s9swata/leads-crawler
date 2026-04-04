"""CLI commands for lead-gen."""

import asyncio
import hashlib
import json
from datetime import datetime
from typing import Optional

import click
from tqdm import tqdm

from src.cli.errors import (
    APIKeyError,
    ConfigurationError,
    LeadGenError,
    NetworkError,
    RateLimitError,
    ScrapingError,
)

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
from src.storage.checkpoint import CheckpointService, CheckpointStatus
from src.core.signals import setup_signal_handlers, set_cleanup_callback


@click.command(name="search")
@click.option("--query", required=True, help="Search query for finding leads")
@click.option("--location", help="Location to search in")
@click.option("--limit", default=10, help="Maximum number of results")
@click.option(
    "--ingest/--no-ingest",
    default=False,
    help="Ingest results to database for later scraping",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview without executing",
)
def search(query, location, limit, ingest, dry_run):
    """Search for business leads based on query and location."""
    # Dry-run mode: skip API key check
    if dry_run:
        asyncio.run(_search(query, location, limit, ingest, None, dry_run))
        return

    settings = Settings()
    if not settings.serper_api_key:
        raise click.ClickException(
            "SERPER_API_KEY not set. Get one at https://serper.dev/ and set it in your .env file."
        )

    # Set up signal handlers for graceful shutdown
    asyncio.run(_search(query, location, limit, ingest, settings, dry_run))


async def _search(
    query: str, location: str, limit: int, ingest: bool, settings, dry_run: bool = False
):
    """Execute search asynchronously."""
    from src.search.adapters import SerperAdapter

    # Dry-run mode: show what would happen without executing
    if dry_run:
        full_query = f"{query} {location}" if location else query
        click.echo("=== DRY RUN MODE ===")
        click.echo(f"Would search for: {full_query}")
        click.echo(f"Location: {location or 'None'}")
        click.echo(f"Limit: {limit} results")
        click.echo(f"Ingest to database: {ingest}")
        click.echo("=====================")
        return

    # Set up signal handlers with checkpoint save
    checkpoint_service = CheckpointService()

    def save_checkpoint():
        """Save checkpoint on interrupt."""
        try:
            checkpoint_service.save_progress(
                "search",
                job_id,
                completed_results,
                [],
                CheckpointStatus.INTERRUPTED.value,
            )
        except Exception:
            pass  # Best effort

    setup_signal_handlers(save_checkpoint)
    set_cleanup_callback(save_checkpoint)

    adapter = SerperAdapter(settings.serper_api_key)

    if location:
        full_query = f"{query} {location}"
    else:
        full_query = query

    click.echo(f"Searching for: {full_query}")

    # Generate job_id from query hash + timestamp
    query_hash = hashlib.sha256(full_query.encode()).hexdigest()[:16]
    job_id = f"{query_hash}_{datetime.utcnow().strftime('%Y%m%d')}"

    # Check for existing checkpoint to resume
    completed_results = []
    start_index = 0

    if checkpoint_service.is_resumable("search", job_id):
        checkpoint = checkpoint_service.load_checkpoint("search", job_id)
        if checkpoint:
            completed_results = checkpoint.completed_items or []
            start_index = len(completed_results)
            click.echo(
                f"Resuming from checkpoint... {start_index} results already completed."
            )

    # Adjust limit to account for already completed results
    adjusted_limit = limit + start_index

    try:
        # Show progress bar during search
        with tqdm(
            total=adjusted_limit, desc="Searching", unit="results", leave=True
        ) as pbar:
            # Skip already completed results if resuming
            for i in range(start_index):
                pbar.update(1)

            results = await adapter.search(full_query, adjusted_limit)
            new_results = results[start_index:]

            for result in new_results:
                completed_results.append(
                    {
                        "title": result.title,
                        "url": result.url,
                        "snippet": result.snippet,
                    }
                )
                pbar.update(1)

                # Save checkpoint after each page
                checkpoint_service.save_progress(
                    "search", job_id, completed_results, [], "running"
                )
    except LeadGenError as e:
        # Save checkpoint on failure
        checkpoint_service.save_progress(
            "search", job_id, completed_results, [{"error": str(e)}], "failed"
        )
        click.echo(click.style(f"Error: {e.user_message}", fg="red"), err=True)
        raise click.ClickException(e.user_message)
    except Exception as e:
        # Save checkpoint on failure
        checkpoint_service.save_progress(
            "search", job_id, completed_results, [{"error": str(e)}], "failed"
        )
        raise click.ClickException(f"Search failed: {e}")
    finally:
        # Ensure progress bar is closed
        try:
            tqdm._instances.clear()  # type: ignore
        except Exception:
            pass

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

    # Clear checkpoint on successful completion
    checkpoint_service.clear_checkpoint("search", job_id)


@click.command(name="scrape")
@click.option("--url", required=True, help="URL to scrape")
@click.option(
    "--format",
    type=click.Choice(["json", "text"]),
    default="json",
    help="Output format",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview without executing",
)
def scrape(url, format, dry_run):
    """Scrape contact information from a URL."""
    asyncio.run(_scrape(url, format, dry_run))


async def _scrape(url: str, output_format: str, dry_run: bool = False):
    """Execute scrape asynchronously."""
    # Dry-run mode: show what would happen without executing
    if dry_run:
        click.echo("=== DRY RUN MODE ===")
        click.echo(f"Would scrape: {url}")
        click.echo("With extractors: email, phone, social, website")
        click.echo("Would store results to database")
        click.echo("=====================")
        return

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

    # Use URL as job_id for scrape operations
    job_id = url
    checkpoint_service = CheckpointService()
    completed_items = []
    failed_items = []

    # Set up signal handlers with checkpoint save
    def save_checkpoint():
        """Save checkpoint on interrupt."""
        try:
            checkpoint_service.save_progress(
                "scrape",
                job_id,
                completed_items,
                failed_items,
                CheckpointStatus.INTERRUPTED.value,
            )
        except Exception:
            pass  # Best effort

    setup_signal_handlers(save_checkpoint)
    set_cleanup_callback(save_checkpoint)

    # Check for existing checkpoint to resume
    if checkpoint_service.is_resumable("scrape", job_id):
        checkpoint = checkpoint_service.load_checkpoint("scrape", job_id)
        if checkpoint:
            completed_items = checkpoint.completed_items or []
            failed_items = checkpoint.failed_items or []
            click.echo(f"Resuming scrape from {len(completed_items)} completed URLs...")

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

        # Track completed item
        completed_items.append(result)

        # Save checkpoint after each successful scrape
        checkpoint_service.save_progress(
            "scrape", job_id, completed_items, failed_items, "running"
        )

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
    except LeadGenError as e:
        # Track failed item and save checkpoint
        failed_items.append({"url": url, "error": str(e)})
        checkpoint_service.save_progress(
            "scrape", job_id, completed_items, failed_items, "failed"
        )
        click.echo(click.style(f"Error: {e.user_message}", fg="red"), err=True)
        raise click.ClickException(e.user_message)
    except Exception as e:
        # Track failed item and save checkpoint
        failed_items.append({"url": url, "error": str(e)})
        checkpoint_service.save_progress(
            "scrape", job_id, completed_items, failed_items, "failed"
        )
        raise click.ClickException(f"Scrape failed: {e}")
    finally:
        # Clear checkpoint on successful completion (moved here for proper cleanup)
        if not failed_items:
            checkpoint_service.clear_checkpoint("scrape", job_id)
        # Ensure progress bars are closed
        try:
            from tqdm import tqdm

            tqdm._instances.clear()  # type: ignore
        except Exception:
            pass
        await crawler.close()


@click.command(name="init")
def init():
    """Initialize a new lead generation project with default config."""
    from src.storage.database import init_db

    click.echo("Initializing lead-gen project...")
    init_db()
    click.echo("Database tables created ✓")


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
            if lead.business_category:
                click.echo(f"  Category: {lead.business_category}")
            if lead.email:
                click.echo(f"  Email: {lead.email}")
            if lead.website:
                click.echo(f"  Website: {lead.website}")
            if lead.phone:
                click.echo(f"  Phone: {lead.phone}")
            if lead.address:
                click.echo(f"  Address: {lead.address}")
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
