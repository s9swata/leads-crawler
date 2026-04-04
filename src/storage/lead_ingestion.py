"""Lead ingestion service with deduplication."""

from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from src.core.types import Lead
from src.storage.database import session_scope
from src.storage.deduplicator import Deduplicator
from src.storage.lead_repo import LeadRepository


class LeadIngestionService:
    """Service for ingesting leads with deduplication."""

    def __init__(self):
        """Initialize the ingestion service."""
        self._deduplicator = Deduplicator()

    def ingest(
        self,
        data: dict,
        company_name: Optional[str] = None,
        source: str = "scrape",
        source_url: Optional[str] = None,
        address: Optional[str] = None,
        business_category: Optional[str] = None,
    ) -> tuple[int, int, list[Lead]]:
        """
        Ingest leads from scraped data with deduplication.

        Args:
            data: Dict with keys: url, emails, phones, social, websites, address
            company_name: Optional company name (extracted from URL domain if not provided)
            source: Source of leads (default: "scrape")
            source_url: URL where data was scraped from
            address: Optional physical address
            business_category: Optional business category

        Returns:
            Tuple of (added_count, duplicate_count, leads)
        """
        url = data.get("url", "")
        emails = data.get("emails", [])
        phones = data.get("phones", [])
        social = data.get("social", [])
        websites = data.get("websites", [])
        scraped_address = data.get("address") or address

        if not company_name and url:
            domain = self._extract_domain_name(url)
            company_name = domain

        leads = []
        added_count = 0
        duplicate_count = 0

        if not emails and not websites and not phones and not social:
            return 0, 0, []

        lead_id = self._generate_lead_id(url)
        primary_email = emails[0] if emails else None
        primary_website = websites[0] if websites else None
        primary_phone = phones[0] if phones else None
        linkedin = self._extract_linkedin(social)

        with session_scope() as session:
            repo = LeadRepository(session)

            lead = Lead(
                id=lead_id,
                company_name=company_name or "Unknown",
                email=primary_email,
                website=primary_website,
                phone=primary_phone,
                linkedin=linkedin,
                address=scraped_address,
                business_category=business_category,
                source=source,
                source_url=source_url or url,
                discovered_at=datetime.utcnow(),
                scraped_at=datetime.utcnow(),
            )

            duplicate = self._deduplicator.find_duplicate(lead, repo)

            if duplicate:
                duplicate_count = 1
            else:
                repo.add(lead)
                leads.append(lead)
                added_count = 1

        return added_count, duplicate_count, leads

    def _extract_domain_name(self, url: str) -> str:
        """Extract domain name from URL for company name."""
        if not url:
            return "Unknown"
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        if domain:
            parts = domain.split(".")
            if len(parts) >= 2:
                return parts[0].capitalize()
            return domain.capitalize()
        return "Unknown"

    def _extract_linkedin(self, social: list[str]) -> Optional[str]:
        """Extract LinkedIn URL from social links."""
        for s in social or []:
            if "linkedin.com" in s.lower():
                return s
        return None

    def _generate_lead_id(self, url: str) -> str:
        """Generate a unique lead ID from URL."""
        if not url:
            from uuid import uuid4

            return f"lead-{uuid4().hex[:8]}"
        domain = self._extract_domain_name(url)
        return f"lead-{domain.lower()}"
