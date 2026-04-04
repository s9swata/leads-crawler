"""Website URL extractor."""

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class WebsiteExtractor:
    """Extract website URLs from HTML content."""

    def extract_from_html(self, html: str, base_url: str = "") -> list[str]:
        """Extract absolute URLs from HTML content.

        Args:
            html: HTML content as string
            base_url: Base URL for resolving relative URLs

        Returns:
            List of absolute URLs found in the page
        """
        soup = BeautifulSoup(html, "lxml")
        urls = set()

        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if not href:
                continue

            if href.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue

            if base_url:
                absolute_url = urljoin(base_url, href)
            else:
                absolute_url = href

            # Skip URLs that look like email addresses
            if "@" in absolute_url:
                continue

            parsed = urlparse(absolute_url)
            if parsed.scheme in ("http", "https") and parsed.netloc:
                # Skip URLs with invalid domains (single char, no dots, etc.)
                netloc = parsed.netloc.lower()
                if "." not in netloc:
                    continue
                # Skip common non-business domains
                if any(
                    skip in netloc
                    for skip in [
                        "youtube.com",
                        "facebook.com",
                        "instagram.com",
                        "twitter.com",
                        "linkedin.com",
                        "tiktok.com",
                        "whatsapp.com",
                        "t.me",
                        "wa.me",
                    ]
                ):
                    continue
                urls.add(absolute_url)

        return sorted(urls)
