"""Reddit lead extractor - finds business leads from Reddit posts and profiles."""

import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from src.extraction.extractors.email import EmailExtractor
from src.extraction.extractors.phone import PhoneExtractor
from src.extraction.extractors.social import SocialExtractor
from src.extraction.extractors.website import WebsiteExtractor
from src.extraction.extractors.phone import is_valid_phone
from src.core.types import Lead
from src.storage.lead_ingestion import LeadIngestionService

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
WEBSITE_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.[a-zA-Z]{2,}(?:/[^\s<>\(\)\[\]{}]*)?)"
)

VALID_TLDS = {
    "com",
    "co",
    "io",
    "dev",
    "net",
    "org",
    "app",
    "ai",
    "in",
    "uk",
    "de",
    "fr",
    "au",
    "ca",
    "us",
    "me",
    "info",
    "biz",
    "agency",
    "studio",
    "design",
    "tech",
    "digital",
    "online",
    "site",
    "store",
    "xyz",
    "ma",
    "fi",
    "eu",
    "co.uk",
    "co.in",
    "com.au",
    "com.br",
    "co.jp",
}

SKIP_DOMAINS = {
    "reddit.com",
    "redd.it",
    "redditmedia.com",
    "redditstatic.com",
    "imgur.com",
    "youtube.com",
    "youtu.be",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "linkedin.com",
    "google.com",
    "amazon.com",
    "github.com",
    "medium.com",
    "wordpress.com",
    "wix.com",
    "squarespace.com",
    "shopify.com",
    "etsy.com",
    "fiverr.com",
    "upwork.com",
    "proton.me",
    "gmail.com",
    "drive.google",
    "docs.google",
    "forms.google",
    "sheets.google",
    "artstation.com",
    "behance.net",
    "figma.com",
    "dribbble.com",
    "twitch.tv",
    "discord.com",
    "slack.com",
    "zoom.us",
    "calendly.com",
    "notion.so",
    "trello.com",
    "vercel.app",
    "netlify.app",
    "herokuapp.com",
    "pages.dev",
    "github.io",
}

TECH_KEYWORDS = {
    "node.js",
    "next.js",
    "react.js",
    "vue.js",
    "angular.js",
    "django",
    "flask",
    "wordpress",
    "shopify",
    "wix",
    "squarespace",
    "webflow",
    "framer",
}


class RedditLeadExtractor:
    """Extracts business leads from Reddit posts and text."""

    def __init__(self):
        self.email_extractor = EmailExtractor()
        self.phone_extractor = PhoneExtractor()
        self.social_extractor = SocialExtractor()
        self.website_extractor = WebsiteExtractor()

    def extract_from_text(self, text: str) -> dict:
        """Extract contact info from plain text."""
        emails = list(set(EMAIL_PATTERN.findall(text)))
        raw_urls = list(set(WEBSITE_PATTERN.findall(text)))

        valid_urls = []
        for url in raw_urls:
            clean_url = url.rstrip(")/>,.;")
            if not clean_url.startswith(("http://", "https://")):
                clean_url = f"https://{clean_url}"
            try:
                parsed = urlparse(clean_url)
                netloc = parsed.netloc.lower()
                if not netloc or "." not in netloc:
                    continue
                if any(skip in netloc for skip in SKIP_DOMAINS):
                    continue
                domain_parts = netloc.split(".")
                if len(domain_parts) < 2:
                    continue
                tld = domain_parts[-1]
                root = domain_parts[-2]
                if root in TECH_KEYWORDS:
                    continue
                if tld not in VALID_TLDS:
                    continue
                valid_urls.append(clean_url)
            except Exception:
                continue

        phones = self.phone_extractor.extract_from_text(text)
        social = self.social_extractor.extract_from_text(text)

        return {
            "emails": emails,
            "phones": phones,
            "websites": valid_urls,
            "social": social,
        }

    def process_post(
        self,
        post: dict,
        source: str = "reddit",
        business_category: Optional[str] = None,
        require_email_and_phone: bool = False,
    ) -> Optional[Lead]:
        """Process a Reddit post and extract lead info.

        Args:
            post: Post dict from RedditAdapter
            source: Source identifier
            business_category: Optional category
            require_email_and_phone: Only return lead if both exist

        Returns:
            Lead object or None if no contact info found
        """
        text = f"{post.get('title', '')} {post.get('selftext', '')}"
        contact = self.extract_from_text(text)

        emails = contact["emails"]
        phones = contact["phones"]
        websites = contact["websites"]
        social = contact["social"]

        primary_email = emails[0] if emails else None
        primary_phone = phones[0] if phones else None
        primary_website = websites[0] if websites else None
        linkedin = None
        for s in social:
            if "linkedin.com" in s.lower():
                linkedin = s
                break

        if require_email_and_phone:
            if not primary_email or not primary_phone:
                return None
            if not is_valid_phone(primary_phone):
                return None

        if (
            not primary_email
            and not primary_website
            and not primary_phone
            and not linkedin
        ):
            return None

        company_name = self._extract_company_name(post, primary_email, primary_website)

        lead_id = f"reddit-{post.get('id', post.get('author', 'unknown'))}"

        return Lead(
            id=lead_id,
            company_name=company_name,
            email=primary_email,
            website=primary_website,
            phone=primary_phone,
            linkedin=linkedin,
            address=None,
            business_category=business_category,
            source=source,
            source_url=post.get("permalink", ""),
            discovered_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
        )

    def ingest_post(
        self,
        post: dict,
        source: str = "reddit",
        business_category: Optional[str] = None,
        require_email_and_phone: bool = False,
    ) -> tuple[bool, str]:
        """Process and ingest a Reddit post as a lead.

        Returns:
            Tuple of (success, message)
        """
        lead = self.process_post(
            post, source, business_category, require_email_and_phone
        )
        if not lead:
            return False, "No contact info found"

        try:
            ingestion = LeadIngestionService()
            added, duplicates, _ = ingestion.ingest(
                data={
                    "url": post.get("permalink", ""),
                    "emails": [lead.email] if lead.email else [],
                    "phones": [lead.phone] if lead.phone else [],
                    "social": [lead.linkedin] if lead.linkedin else [],
                    "websites": [lead.website] if lead.website else [],
                },
                company_name=lead.company_name,
                source=source,
                source_url=lead.source_url,
                business_category=business_category,
            )
            if added:
                return True, f"Added: {lead.company_name}"
            else:
                return False, f"Duplicate: {lead.company_name}"
        except Exception as e:
            return False, f"Error: {e}"

    def _extract_company_name(
        self, post: dict, email: Optional[str], website: Optional[str]
    ) -> str:
        """Extract company name from post data."""
        if email:
            domain = email.split("@")[1]
            name = domain.split(".")[0]
            return name.replace("-", " ").title()

        if website:
            try:
                parsed = urlparse(website)
                domain = parsed.netloc
                if domain.startswith("www."):
                    domain = domain[4:]
                name = domain.split(".")[0]
                return name.replace("-", " ").title()
            except Exception:
                pass

        author = post.get("author", "unknown")
        return author.replace("-", " ").replace("_", " ").title()
