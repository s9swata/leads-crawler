"""Source adapter package."""

from src.extraction.adapters.base import SourceAdapter
from src.extraction.adapters.crawl4ai_adapter import Crawl4aiAdapter

__all__ = ["SourceAdapter", "Crawl4aiAdapter"]
