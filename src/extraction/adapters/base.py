"""Source adapter base class."""

from abc import ABC, abstractmethod
from typing import Optional

from src.core.rate_limiter import RateLimiter
from src.core.robots import RobotsTxtParser


class SourceAdapter(ABC):
    """Abstract base class for source adapters (Strategy pattern)."""

    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        robots_parser: Optional[RobotsTxtParser] = None,
    ):
        """Initialize source adapter.

        Args:
            rate_limiter: Rate limiter instance
            robots_parser: Robots.txt parser instance
        """
        self.rate_limiter = rate_limiter
        self.robots_parser = robots_parser

    @abstractmethod
    async def fetch(self, url: str) -> str:
        """Fetch content from URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this source adapter.

        Returns:
            Source adapter name
        """
        pass

    async def fetch_if_allowed(self, url: str) -> str:
        """Fetch content if allowed by robots.txt.

        Args:
            url: URL to fetch

        Returns:
            HTML content if allowed

        Raises:
            ValueError: If URL is not allowed by robots.txt
        """
        if self.robots_parser:
            can_fetch = await self.robots_parser.can_fetch(url)
            if not can_fetch:
                raise ValueError(f"URL not allowed by robots.txt: {url}")

        if self.rate_limiter:
            from urllib.parse import urlparse

            domain = urlparse(url).netloc
            await self.rate_limiter.acquire(domain)

        return await self.fetch(url)
