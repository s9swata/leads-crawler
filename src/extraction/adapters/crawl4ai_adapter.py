"""Crawl4ai adapter implementation."""

from crawl4ai import AsyncWebCrawler

from src.core.retry import retry
from src.extraction.adapters.base import SourceAdapter


class Crawl4aiAdapter(SourceAdapter):
    """Crawl4ai implementation of SourceAdapter."""

    def __init__(self, crawler: AsyncWebCrawler, **kwargs):
        """Initialize Crawl4ai adapter.

        Args:
            crawler: AsyncWebCrawler instance
            **kwargs: Additional arguments passed to base class
        """
        super().__init__(**kwargs)
        self.crawler = crawler

    @retry(
        max_retries=2,
        initial_backoff=1.0,
        backoff_factor=2.0,
        retry_on=(Exception,),
    )
    async def fetch(self, url: str) -> str:
        """Fetch HTML content from URL using Crawl4ai with retry on failure.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        result = await self.crawler.arun(
            url=url,
            timeout=15.0,
        )
        if result.success:
            return result.html
        raise ValueError(f"Failed to fetch {url}: {result.error}")

    def get_source_name(self) -> str:
        """Get the source adapter name.

        Returns:
            "crawl4ai"
        """
        return "crawl4ai"
