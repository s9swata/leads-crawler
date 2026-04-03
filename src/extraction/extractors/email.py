"""Email extractor using regex patterns."""

import re
from typing import Optional


class EmailExtractor:
    """Extracts email addresses from HTML or text."""

    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

    def extract_from_text(self, text: str) -> list[str]:
        """Extract email addresses from plain text.

        Args:
            text: Text content to extract emails from

        Returns:
            List of unique email addresses found
        """
        matches = re.findall(self.EMAIL_PATTERN, text, re.IGNORECASE)
        return list(set(matches))

    def extract_from_html(self, html: str) -> list[str]:
        """Extract email addresses from HTML content.

        Args:
            html: HTML content to extract emails from

        Returns:
            List of unique email addresses found
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator=" ")
        return self.extract_from_text(text)
