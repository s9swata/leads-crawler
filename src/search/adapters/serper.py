import httpx

from src.core.retry import retry
from src.search.adapters.base import SearchAdapter
from src.search.models import SearchResult


class SerperAdapter(SearchAdapter):
    BASE_URL = "https://google.serper.dev/search"
    MAX_RESULTS_PER_PAGE = 10

    def __init__(self, api_key: str):
        self.api_key = api_key

    @retry(
        max_retries=5,
        initial_backoff=1.0,
        backoff_factor=2.0,
        retry_on=(httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException),
    )
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for results with retry on failure."""
        headers = {"X-API-Key": self.api_key}
        all_results: list[SearchResult] = []
        start = 0

        async with httpx.AsyncClient() as client:
            while len(all_results) < limit:
                remaining = limit - len(all_results)
                num_results = min(remaining, self.MAX_RESULTS_PER_PAGE)

                data = {"q": query, "num": num_results, "start": start}

                response = await client.post(
                    self.BASE_URL, headers=headers, json=data, timeout=30.0
                )
                response.raise_for_status()

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

    def get_provider_name(self) -> str:
        return "serper"
