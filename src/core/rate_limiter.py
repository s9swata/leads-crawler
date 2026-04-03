"""Rate limiting with crawl-delay respect."""

import asyncio
import logging
from collections import defaultdict
from typing import Optional

from src.config.settings import Settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with crawl-delay respect using sliding window algorithm."""

    def __init__(self, settings: Settings):
        """Initialize rate limiter.

        Args:
            settings: Settings instance containing rate limit configuration
        """
        self.requests_per_second = settings.requests_per_second
        self.respect_crawl_delay = settings.respect_robots_txt
        self._domain_delays: dict[str, float] = {}
        self._request_timestamps: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str) -> None:
        """Acquire permission to make a request to the domain.

        Args:
            domain: The domain to acquire rate limit for
        """
        async with self._lock:
            delay = self._get_delay(domain)
            timestamps = self._request_timestamps[domain]

            now = asyncio.get_event_loop().time()
            window_start = now - 1.0

            timestamps = [ts for ts in timestamps if ts > window_start]
            self._request_timestamps[domain] = timestamps

            if len(timestamps) >= self._requests_per_second(domain):
                sleep_time = timestamps[0] - window_start + 0.01
                if sleep_time > 0:
                    await self._log_throttle(domain, sleep_time)
                    await asyncio.sleep(sleep_time)

            self._request_timestamps[domain].append(now)

    def _requests_per_second(self, domain: str) -> float:
        """Get requests per second for a domain.

        Args:
            domain: The domain to get rate for

        Returns:
            Requests per second (may be reduced by crawl-delay)
        """
        base_rate = self.requests_per_second
        domain_delay = self._domain_delays.get(domain)
        if domain_delay and self.respect_crawl_delay and domain_delay > 0:
            return min(base_rate, 1.0 / domain_delay)
        return base_rate

    def _get_delay(self, domain: str) -> float:
        """Get the current delay setting for a domain.

        Args:
            domain: The domain to get delay for

        Returns:
            Delay in seconds
        """
        return self._domain_delays.get(domain, 0.0)

    def set_domain_delay(self, domain: str, delay: Optional[float]) -> None:
        """Set per-domain crawl-delay from robots.txt.

        Args:
            domain: The domain to set delay for
            delay: Crawl-delay in seconds, or None to clear
        """
        if delay is not None and delay > 0:
            self._domain_delays[domain] = delay
            logger.info(f"Crawl-delay for {domain}: {delay}s")

    async def _log_throttle(self, domain: str, delay: float) -> None:
        """Log when throttling occurs.

        Args:
            domain: The domain being throttled
            delay: The delay in seconds
        """
        logger.info(f"Throttling request to {domain}, delay: {delay:.2f}s")
