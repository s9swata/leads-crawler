"""Batch lead generation across multiple categories and locations."""

import asyncio
import random
import time

import click
from tqdm import tqdm

from src.config.settings import Settings
from src.storage.database import session_scope
from src.export.csv_generator import export_csv


CATEGORIES = {
    "restaurants": [
        "restaurant",
        "cafe",
        "bistro",
        "fine dining",
        "pizza restaurant",
        "italian restaurant",
        "chinese restaurant",
        "indian restaurant",
        "bakery",
        "coffee shop",
    ],
    "gyms": [
        "gym",
        "fitness center",
        "yoga studio",
        "crossfit",
        "pilates studio",
        "health club",
        "boxing gym",
        "dance studio",
    ],
    "salons": [
        "salon",
        "beauty salon",
        "hair salon",
        "spa",
        "barber shop",
        "nail salon",
        "beauty parlor",
        "wellness center",
    ],
    "clinics": [
        "clinic",
        "dental clinic",
        "doctor",
        "healthcare clinic",
        "physiotherapy clinic",
        "dermatology clinic",
        "eye clinic",
        "diagnostic center",
    ],
    "real_estate": [
        "real estate agency",
        "property dealer",
        "real estate broker",
        "property consultant",
        "real estate developer",
        "property management",
        "real estate agent",
    ],
    "coaching": [
        "coaching institute",
        "tuition center",
        "coaching classes",
        "training center",
        "education center",
        "language school",
        "test preparation",
        "career coaching",
    ],
}

LOCATIONS = [
    "Pune",
    "Mumbai",
    "Delhi",
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Lucknow",
    "Chandigarh",
    "Noida",
    "Gurgaon",
    "Nagpur",
    "Indore",
    "Bhopal",
    "Surat",
    "Vadodara",
    "Coimbatore",
    "Kochi",
    "Visakhapatnam",
    "Dehradun",
    "Goa",
]


class BatchScraper:
    """Manages scraping using agent-browser for reliable scraping."""

    def __init__(self):
        self.adapter = None
        self.email_extractor = None
        self.phone_extractor = None
        self.social_extractor = None
        self.website_extractor = None
        self.address_extractor = None

    async def start(self):
        """Initialize adapter and extractors."""
        from src.extraction.adapters.agent_browser_adapter import AgentBrowserAdapter
        from src.extraction.extractors import (
            EmailExtractor,
            PhoneExtractor,
            SocialExtractor,
            WebsiteExtractor,
            AddressExtractor,
        )

        self.adapter = AgentBrowserAdapter(timeout=15)

        self.email_extractor = EmailExtractor()
        self.phone_extractor = PhoneExtractor()
        self.social_extractor = SocialExtractor()
        self.website_extractor = WebsiteExtractor()
        self.address_extractor = AddressExtractor()

    async def scrape(self, url: str) -> dict | None:
        """Scrape a single URL and return extracted data."""
        try:
            html = await self.adapter.fetch(url)

            emails = self.email_extractor.extract_from_html(html)
            phones = self.phone_extractor.extract_from_html(html)
            social = self.social_extractor.extract_from_html(html)
            websites = self.website_extractor.extract_from_html(html, base_url=url)
            address = self.address_extractor.extract_from_html(html)

            return {
                "url": url,
                "emails": emails,
                "phones": phones,
                "social": social,
                "websites": websites,
                "address": address,
            }
        except Exception:
            return None

    async def close(self):
        """Clean up."""
        pass


URL_SKIP_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "facebook.com",
    "fb.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "pinterest.com",
    "snapchat.com",
    "linkedin.com",
    "wa.me",
    "t.me",
    "whatsapp.com",
    "reddit.com",
    "tripadvisor.com",
    "tripadvisor.in",
    "swiggy.com",
    "zomato.com",
    "eazydiner.com",
    "tripoto.com",
    "wanderlog.com",
    "balancegurus.com",
    "cntraveller.in",
    "yelp.com",
    "justdial.com",
    "sulekha.com",
    "google.com",
    "google.co.in",
    "wikipedia.org",
    "quora.com",
]


def _is_scrapable_url(url: str) -> bool:
    """Check if URL is worth scraping for business contact info."""
    url_lower = url.lower()
    # Skip known non-business domains
    for domain in URL_SKIP_DOMAINS:
        if domain in url_lower:
            return False
    # Skip image/video files
    if any(
        url_lower.endswith(ext)
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".avi"]
    ):
        return False
    # Skip very short URLs that are likely not business sites
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if len(parsed.path) < 3 and parsed.path not in ["/", ""]:
        return False
    return True


async def _search_urls(
    query: str, location: str, limit: int, api_key: str
) -> list[str]:
    """Search and return unique URLs from results."""
    from src.search.adapters import SerperAdapter

    adapter = SerperAdapter(api_key)
    full_query = f"{query} {location}"

    try:
        results = await adapter.search(full_query, limit)
        return [r.url for r in results if r.url]
    except Exception:
        return []


def _count_leads_with_emails() -> int:
    """Count leads with emails in database."""
    from src.storage.models import Lead as LeadModel

    with session_scope() as session:
        return session.query(LeadModel).filter(LeadModel.email.isnot(None)).count()


def _count_leads_with_email_and_phone() -> int:
    """Count leads with both email and valid phone in database."""
    from src.storage.models import Lead as LeadModel
    from src.extraction.extractors.phone import is_valid_phone

    with session_scope() as session:
        leads = (
            session.query(LeadModel)
            .filter(LeadModel.email.isnot(None), LeadModel.phone.isnot(None))
            .all()
        )
        return sum(1 for l in leads if is_valid_phone(l.phone))


async def _run_batch(
    selected_categories: list[str],
    selected_locations: list[str],
    target: int,
    delay: float,
    search_limit: int,
    require_email_and_phone: bool = False,
):
    """Run the batch lead generation in a single async context."""
    settings = Settings()
    api_key = settings.serper_api_key

    # Build search queries
    queries = []
    for cat in selected_categories:
        for query in CATEGORIES[cat]:
            for loc in selected_locations:
                queries.append((query, loc, cat))

    random.shuffle(queries)

    # Track progress
    if require_email_and_phone:
        existing = _count_leads_with_email_and_phone()
        qualifier_label = "email + phone"
    else:
        existing = _count_leads_with_emails()
        qualifier_label = "emails"

    leads_qualified = existing
    scraped_urls = set()
    total_searches = 0
    total_scrapes = 0
    failed_scrapes = 0
    success_scrapes = 0

    click.echo(f"Existing leads with {qualifier_label}: {existing}")
    remaining = max(0, target - existing)
    if remaining == 0:
        return existing, 0, 0, 0, 0

    click.echo(f"Need {remaining} more leads with {qualifier_label}\n")
    click.echo("Starting batch lead generation...\n")

    # Single crawler instance
    scraper = BatchScraper()
    await scraper.start()

    try:
        for query, location, category in tqdm(queries, desc="Processing queries"):
            if leads_qualified >= target:
                click.echo(
                    f"\nTarget of {target} leads with {qualifier_label} reached!"
                )
                break

            total_searches += 1

            # Search for URLs
            urls = await _search_urls(query, location, search_limit, api_key)

            if not urls:
                continue

            # Scrape each URL
            for url in urls:
                if leads_qualified >= target:
                    break

                if url in scraped_urls:
                    continue

                # Skip URLs that are unlikely to have business contact info
                if not _is_scrapable_url(url):
                    continue

                scraped_urls.add(url)
                total_scrapes += 1

                # Add delay
                await asyncio.sleep(delay + random.uniform(0, 1))

                # Scrape with shared crawler
                result = await scraper.scrape(url)

                if not result or not result.get("emails"):
                    failed_scrapes += 1
                    continue

                if require_email_and_phone and not result.get("phones"):
                    failed_scrapes += 1
                    continue

                success_scrapes += 1

                # Ingest leads
                from src.storage.lead_ingestion import LeadIngestionService

                try:
                    ingestion_service = LeadIngestionService()
                    added, duplicates, leads = ingestion_service.ingest(
                        data=result,
                        source="batch",
                        source_url=url,
                        business_category=category,
                    )

                    if added:
                        lead = leads[0]
                        has_email = bool(lead.email)
                        has_phone = bool(lead.phone)
                        if require_email_and_phone:
                            from src.extraction.extractors.phone import is_valid_phone

                            has_phone = has_phone and is_valid_phone(lead.phone)

                        if has_email and has_phone:
                            leads_qualified += 1
                            click.echo(
                                f"  [{category}] {url} - {len(result['emails'])} email(s), {len(result['phones'])} phone(s)"
                            )
                        elif not require_email_and_phone and has_email:
                            leads_qualified += 1
                            click.echo(
                                f"  [{category}] {url} - {len(result['emails'])} email(s)"
                            )
                except Exception as e:
                    # Skip leads that fail validation (bad URLs, etc.)
                    click.echo(f"  ✗ {url} - Ingestion error: {e}")
                    failed_scrapes += 1
                    continue

    finally:
        await scraper.close()

    return (
        leads_qualified,
        total_searches,
        total_scrapes,
        success_scrapes,
        failed_scrapes,
    )


@click.command(name="batch")
@click.option(
    "--categories",
    default="all",
    help="Comma-separated categories (all,restaurants,gyms,salons,clinics,real_estate,coaching)",
)
@click.option(
    "--locations",
    default="",
    help="Comma-separated locations (default: all 23 Indian cities)",
)
@click.option(
    "--target",
    default=1000,
    help="Target number of leads with emails (default: 1000)",
)
@click.option(
    "--output",
    "-o",
    default="leads_batch_export.csv",
    help="Output CSV file path",
)
@click.option(
    "--delay",
    default=2.0,
    help="Delay between scrapes in seconds (default: 2.0)",
)
@click.option(
    "--search-limit",
    default=10,
    help="Max search results per query (default: 10)",
)
@click.option(
    "--require-email-and-phone",
    is_flag=True,
    default=False,
    help="Only save leads that have both email AND valid phone number",
)
def batch(
    categories, locations, target, output, delay, search_limit, require_email_and_phone
):
    """Batch generate leads across multiple categories and locations."""
    settings = Settings()
    if not settings.serper_api_key:
        raise click.ClickException(
            "SERPER_API_KEY not set. Get one at https://serper.dev/"
        )

    # Parse categories
    if categories == "all":
        selected_categories = list(CATEGORIES.keys())
    else:
        selected_categories = [c.strip() for c in categories.split(",")]
        invalid = [c for c in selected_categories if c not in CATEGORIES]
        if invalid:
            raise click.ClickException(f"Invalid categories: {invalid}")

    # Parse locations
    if locations:
        selected_locations = [loc.strip() for loc in locations.split(",")]
    else:
        selected_locations = LOCATIONS

    click.echo(f"Categories: {', '.join(selected_categories)}")
    click.echo(f"Locations: {', '.join(selected_locations)}")
    click.echo(
        f"Target: {target} leads with {'email + phone' if require_email_and_phone else 'emails'}"
    )
    click.echo(f"Output: {output}")
    click.echo("")

    # Run batch in single async context
    (
        leads_qualified,
        total_searches,
        total_scrapes,
        success_scrapes,
        failed_scrapes,
    ) = asyncio.run(
        _run_batch(
            selected_categories,
            selected_locations,
            target,
            delay,
            search_limit,
            require_email_and_phone,
        )
    )

    # Final stats
    click.echo(f"\n{'=' * 60}")
    click.echo(f"BATCH GENERATION COMPLETE")
    click.echo(f"{'=' * 60}")
    click.echo(f"Searches performed: {total_searches}")
    click.echo(f"URLs scraped: {total_scrapes}")
    click.echo(f"Successful scrapes: {success_scrapes}")
    click.echo(f"Failed scrapes: {failed_scrapes}")
    click.echo(
        f"Total leads with {'email + phone' if require_email_and_phone else 'emails'}: {leads_qualified}"
    )
    click.echo(f"{'=' * 60}")

    # Export
    click.echo(f"\nExporting leads to {output}...")
    _export_current_leads(output, require_email_and_phone=require_email_and_phone)
    click.echo(f"Done! File saved to: {output}")


def _export_current_leads(output: str, require_email_and_phone: bool = False):
    """Export leads to CSV."""
    from src.storage.models import Lead as LeadModel
    from src.extraction.extractors.phone import is_valid_phone

    with session_scope() as session:
        if require_email_and_phone:
            leads_list = (
                session.query(LeadModel)
                .filter(LeadModel.email.isnot(None), LeadModel.phone.isnot(None))
                .order_by(LeadModel.discovered_at.desc())
                .all()
            )
            leads_list = [l for l in leads_list if is_valid_phone(l.phone)]
        else:
            leads_list = (
                session.query(LeadModel)
                .filter(LeadModel.email.isnot(None))
                .order_by(LeadModel.discovered_at.desc())
                .all()
            )

        if not leads_list:
            click.echo("No leads to export.")
            return

        count = export_csv(leads_list, output, None)
        click.echo(f"Exported {count} leads to {output}")
