import httpx

from src.search.adapters.base import SearchAdapter
from src.search.models import SearchResult


class SerperAdapter(SearchAdapter):
    BASE_URL = "https://google.serper.dev/search"
    MAX_RESULTS_PER_PAGE = 10
    MAX_RETRIES = 5
    INITIAL_BACKOFF = 1.0  # seconds

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        headers = {"X-API-Key": self.api_key}
        all_results: list[SearchResult] = []
        start = 0

        async with httpx.AsyncClient() as client:
            while len(all_results) < limit:
                remaining = limit - len(all_results)
                num_results = min(remaining, self.MAX_RESULTS_PER_PAGE)

                data = {"q": query, "num": num_results, "start": start}

                response = await self._request_with_retry(client, headers, data)

                results = response.json()
                organic = results.get("organic", [])

                if not organic:
                    break

                for item in organic:
                    all_results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                        )
                    )

                # Check if there are more results to fetch
                if len(organic) < num_results:
                    break

                start += num_results

        return all_results[:limit]

    async def _request_with_retry(
        self, client: httpx.AsyncClient, headers: dict, data: dict
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry on rate limit."""
        backoff = self.INITIAL_BACKOFF

        for attempt in range(self.MAX_RETRIES):
            response = await client.post(
                self.BASE_URL, headers=headers, json=data, timeout=30.0
            )

            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                # Rate limited - exponential backoff
                import asyncio

                await asyncio.sleep(backoff)
                backoff *= 2  # Exponential backoff
                continue
            else:
                # Other errors - raise immediately
                response.raise_for_status()

        # If we exhausted retries, raise the last response
        response.raise_for_status()

    def get_provider_name(self) -> str:
        return "serper"
