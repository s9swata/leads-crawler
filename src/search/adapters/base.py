from abc import ABC, abstractmethod

from src.search.models import SearchResult


class SearchAdapter(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass
