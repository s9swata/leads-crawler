"""Deduplicator for email/domain matching."""

from typing import Optional
from urllib.parse import urlparse


class Deduplicator:
    """Lead deduplication by email or domain matching."""

    @staticmethod
    def normalize_email(email: str) -> Optional[str]:
        """Normalize email to lowercase and strip whitespace."""
        if not email:
            return None
        return email.strip().lower()

    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Extract domain from URL, stripping www. prefix."""
        if not url:
            return None
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.lower() if domain else None

    def is_duplicate(self, lead: "Lead", existing: list["Lead"]) -> bool:
        """Check if lead is duplicate against existing leads by email or domain."""
        lead_email = self.normalize_email(lead.email) if lead.email else None
        lead_domain = self.extract_domain(lead.website) if lead.website else None

        for ex in existing:
            if lead_email and ex.email:
                if self.normalize_email(ex.email) == lead_email:
                    return True
            if lead_domain and ex.website:
                if self.extract_domain(ex.website) == lead_domain:
                    return True
        return False

    def find_duplicate(self, lead: "Lead", repo: "LeadRepository") -> Optional["Lead"]:
        """Find a duplicate lead in the repository."""
        if lead.email:
            normalized = self.normalize_email(lead.email)
            if normalized:
                existing = repo.find_by_email(normalized)
                if existing:
                    return existing
        if lead.website:
            domain = self.extract_domain(lead.website)
            if domain:
                existing = repo.find_by_website(lead.website)
                if existing:
                    return existing
        return None
