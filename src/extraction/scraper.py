"""Web scraper using Crawl4ai with rate limiting and robots.txt support."""

import logging
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from src.config.settings import Settings
from src.core.rate_limiter import RateLimiter
from src.core.robots import RobotsTxtParser

logger = logging.getLogger(__name__)


class Scraper:
    """Web scraper using Crawl4ai with integrated rate limiting and robots.txt checking."""

    def __init__(self, settings: Settings):
        """Initialize the scraper.

        Args:
            settings: Settings instance for configuration
        """
        self.settings = settings
        self.rate_limiter = RateLimiter(settings)
        self.robots_parser = RobotsTxtParser(settings)

        self.browser_config = BrowserConfig(
            headless=True, browser_type="chromium", text_mode=True
        )
        self.crawler = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.crawler = AsyncWebCrawler(config=self.browser_config)
        await self.crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)

    async def fetch(self, url: str) -> str | None:
        """Fetch a URL and return its HTML content.

        Args:
            url: The URL to fetch

        Returns:
            HTML string if successful, None otherwise
        """
        domain = urlparse(url).netloc

        if not await self.robots_parser.can_fetch(url):
            logger.warning(f"Blocked by robots.txt: {url}")
            return None

        await self.rate_limiter.acquire(domain)

        result = await self.crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                wait_until="networkidle", page_timeout=30000, scan_full_page=True
            ),
        )

        if result.success:
            logger.info(f"Successfully fetched: {url}")
            return result.html
        else:
            logger.warning(f"Failed to fetch {url}: {result.error_message}")
            return None
