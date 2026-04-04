"""Phone number extractor using regex patterns."""

import re
from typing import Optional


class PhoneExtractor:
    """Extracts phone numbers from HTML or text."""

    PHONE_PATTERNS = [
        r"\+?1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",  # US
        r"\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}",  # International
    ]

    def extract_from_text(self, text: str) -> list[str]:
        """Extract phone numbers from plain text.

        Args:
            text: Text content to extract phone numbers from

        Returns:
            List of unique phone numbers found
        """
        phones = set()
        for pattern in self.PHONE_PATTERNS:
            matches = re.findall(pattern, text)
            phones.update(self._normalize(phone) for phone in matches)
        return list(phones)

    def _normalize(self, phone: str) -> str:
        """Normalize phone number by removing extra whitespace.

        Args:
            phone: Phone number string

        Returns:
            Normalized phone number
        """
        return " ".join(phone.split())

    def extract_from_html(self, html: str) -> list[str]:
        """Extract phone numbers from HTML content.

        Args:
            html: HTML content to extract phone numbers from

        Returns:
            List of unique phone numbers found
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        phones = []
        for a in soup.find_all("a", href=True):
            if a["href"].startswith("tel:"):
                phones.append(a["href"][4:])

        text = soup.get_text(separator=" ")
        phones.extend(self.extract_from_text(text))

        return list(set(phones))


def is_valid_phone(phone: str, min_digits: int = 8) -> bool:
    """Check if a phone number is valid (has minimum digits).

    Args:
        phone: Phone number string
        min_digits: Minimum number of digits required

    Returns:
        True if phone number has at least min_digits digits
    """
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= min_digits
