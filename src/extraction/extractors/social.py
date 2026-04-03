"""Social link extractor for LinkedIn and Twitter/X."""

import re
from typing import Optional


class SocialExtractor:
    """Extracts LinkedIn and Twitter/X links from HTML."""

    LINKEDIN_PATTERN = r"linkedin\.com/(?:in|company|pub)/[a-zA-Z0-9_-]+"
    TWITTER_PATTERN = r"(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+"

    def extract_from_html(self, html: str) -> dict[str, list[str]]:
        """Extract social media links from HTML content.

        Args:
            html: HTML content to extract social links from

        Returns:
            Dictionary with 'linkedin' and 'twitter' keys containing lists of URLs
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        links = [a.get("href") for a in soup.find_all("a", href=True)]

        linkedin = [
            self._normalize_url(link)
            for link in links
            if re.search(self.LINKEDIN_PATTERN, link, re.IGNORECASE)
        ]

        twitter = [
            self._normalize_url(link)
            for link in links
            if re.search(self.TWITTER_PATTERN, link, re.IGNORECASE)
        ]

        return {"linkedin": linkedin, "twitter": twitter}

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by adding https scheme if needed.

        Args:
            url: URL string

        Returns:
            Normalized URL
        """
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return ""
        return url
