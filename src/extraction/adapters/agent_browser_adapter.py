"""Agent-browser adapter for web scraping."""

import subprocess
from typing import Optional

from src.core.retry import retry
from src.extraction.adapters.base import SourceAdapter


class AgentBrowserAdapter(SourceAdapter):
    """Agent-browser implementation of SourceAdapter.

    Uses vercel-labs/agent-browser CLI for scraping.
    No robots.txt enforcement, better JS rendering.
    """

    def __init__(self, timeout: int = 15, **kwargs):
        """Initialize agent-browser adapter.

        Args:
            timeout: Page load timeout in seconds
            **kwargs: Additional arguments passed to base class
        """
        super().__init__(**kwargs)
        self.timeout = timeout

    @retry(
        max_retries=2,
        initial_backoff=1.0,
        backoff_factor=2.0,
        retry_on=(Exception,),
    )
    async def fetch(self, url: str) -> str:
        """Fetch HTML content from URL using agent-browser.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        import asyncio

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._fetch_sync, url)
        return result

    def _fetch_sync(self, url: str) -> str:
        """Synchronous fetch using agent-browser CLI."""
        try:
            # Open URL and wait for network idle
            result = subprocess.run(
                [
                    "agent-browser",
                    "open",
                    url,
                    "--json",
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode != 0:
                raise ValueError(f"Failed to open {url}: {result.stderr}")

            # Get page HTML
            result = subprocess.run(
                [
                    "agent-browser",
                    "get",
                    "html",
                    "body",
                    "--json",
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode != 0:
                raise ValueError(f"Failed to get HTML from {url}: {result.stderr}")

            import json

            data = json.loads(result.stdout)
            if data.get("success"):
                inner = data.get("data", {})
                if isinstance(inner, dict):
                    return inner.get("html", "")
                return str(inner)
            raise ValueError(
                f"Failed to get HTML: {data.get('error', 'Unknown error')}"
            )

        except subprocess.TimeoutExpired:
            # Close browser on timeout
            subprocess.run(["agent-browser", "close"], capture_output=True, timeout=5)
            raise ValueError(f"Timeout fetching {url}")
        finally:
            # Always close browser after fetch
            try:
                subprocess.run(
                    ["agent-browser", "close"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            except Exception:
                pass

    def get_source_name(self) -> str:
        """Get the source adapter name.

        Returns:
            "agent-browser"
        """
        return "agent-browser"
