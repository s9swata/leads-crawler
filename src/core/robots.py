"""Robots.txt parser wrapper."""

import logging
from typing import Optional

import httpx
from protego import Protego

from src.config.settings import Settings

logger = logging.getLogger(__name__)


class RobotsTxtParser:
    """Robots.txt parser with caching."""

    def __init__(self, settings: Settings):
        """Initialize robots.txt parser.

        Args:
            settings: Settings instance containing robots.txt configuration
        """
        self.respect_robots_txt = settings.respect_robots_txt
        self._cache: dict[str, tuple[Protego, float]] = {}
        self._cache_ttl = 3600

    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL is allowed to be fetched.

        Args:
            url: The URL to check
            user_agent: The user agent to check for

        Returns:
            True if URL is allowed, False otherwise
        """
        if not self.respect_robots_txt:
            logger.info(f"Robots.txt: ALLOW {url} (disabled)")
            return True

        try:
            from urllib.parse import urlparse

            domain = urlparse(url).netloc
            protego = await self._get_protego(domain)

            if protego.can_fetch(url, user_agent):
                logger.info(f"Robots.txt: ALLOW {url}")
                return True
            else:
                logger.info(f"Robots.txt: BLOCK {url}")
                return False
        except Exception as e:
            logger.warning(f"Robots.txt check failed for {url}: {e}")
            return True

    async def get_crawl_delay(self, user_agent: str = "*") -> Optional[float]:
        """Get crawl-delay for user agent.

        Args:
            user_agent: The user agent to get delay for

        Returns:
            Crawl-delay in seconds, or None if not specified
        """
        return None

    async def _get_protego(self, domain: str) -> Protego:
        """Get Protego instance for domain, with caching.

        Args:
            domain: The domain to get robots.txt for

        Returns:
            Protego instance
        """
        import time

        now = time.time()
        if domain in self._cache:
            protego, cached_at = self._cache[domain]
            if now - cached_at < self._cache_ttl:
                return protego

        protego = await self._parse_robots_txt(domain)
        self._cache[domain] = (protego, now)
        return protego

    async def _parse_robots_txt(self, domain: str) -> Protego:
        """Fetch and parse robots.txt for a domain.

        Args:
            domain: The domain to fetch robots.txt for

        Returns:
            Protego instance
        """
        robots_url = f"https://{domain}/robots.txt"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(robots_url, timeout=10.0)
                if response.status_code == 200:
                    return Protego(response.text)
            except Exception as e:
                logger.debug(f"Failed to fetch robots.txt for {domain}: {e}")

        # Return empty robots.txt (allows everything)
        return Protego("")
