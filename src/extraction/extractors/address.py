"""Extract physical addresses from HTML content."""

import re
from bs4 import BeautifulSoup


class AddressExtractor:
    """Extract physical addresses from HTML content."""

    def extract_from_html(self, html: str) -> str | None:
        """Extract address from HTML content.

        Looks for addresses in <address> tags, contact sections,
        and footer areas with location indicators.

        Args:
            html: HTML content as string

        Returns:
            Extracted address string or None
        """
        soup = BeautifulSoup(html, "lxml")

        # 1. Check <address> tags first (most reliable)
        address_tags = soup.find_all("address")
        for tag in address_tags:
            text = tag.get_text(separator=" ", strip=True)
            cleaned = self._clean_address(text)
            if cleaned and len(cleaned) > 10:
                return cleaned

        # 2. Look for elements with address-related class/id names
        for tag in soup.find_all(
            ["div", "p", "span", "li"],
            class_=re.compile(r"address|location|contact|footer", re.I),
        ):
            text = tag.get_text(separator=" ", strip=True)
            if self._has_address_indicator(text):
                cleaned = self._clean_address(text)
                if cleaned and 15 < len(cleaned) < 300:
                    return cleaned

        # 3. Look for elements containing address keywords near pincode patterns
        for tag in soup.find_all(["p", "div", "span", "li"]):
            text = tag.get_text(separator=" ", strip=True)
            if not text or len(text) < 20 or len(text) > 300:
                continue

            # Check for Indian pincode (6 digits)
            if re.search(r"\b\d{6}\b", text):
                # Check for address indicators
                if self._has_address_indicator(text):
                    cleaned = self._clean_address(text)
                    if cleaned and 15 < len(cleaned) < 300:
                        return cleaned

        return None

    def _has_address_indicator(self, text: str) -> bool:
        """Check if text contains address-related keywords."""
        lower = text.lower()
        indicators = [
            "address",
            "located at",
            "situated at",
            "find us at",
            "visit us at",
            "our location",
            "office address",
            "studio address",
            "branch address",
            "registered office",
            "correspondence address",
            "head office",
        ]
        return any(ind in lower for ind in indicators)

    def _clean_address(self, text: str) -> str | None:
        """Clean and normalize address text."""
        # Remove extra whitespace and newlines
        text = re.sub(r"\s+", " ", text).strip()

        # Truncate to reasonable address length
        if len(text) > 300:
            # Try to find a natural break point
            text = text[:300].rsplit(" ", 1)[0]

        if len(text) < 10:
            return None

        return text
