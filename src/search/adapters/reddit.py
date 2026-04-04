"""Reddit adapter using public JSON API (no API key required)."""

import asyncio
import time

import httpx

from src.core.retry import retry
from src.search.adapters.base import SearchAdapter
from src.search.models import SearchResult

USER_AGENT = "lead-gen-tool/1.0"


class RedditAdapter(SearchAdapter):
    """Search Reddit using the public JSON API.

    No API key required. Appends .json to Reddit URLs.
    Rate limited to ~1 req/sec to avoid blocks.
    """

    BASE_URL = "https://www.reddit.com/search.json"
    SUBREDDIT_URL = "https://www.reddit.com/r/{subreddit}/{sort}.json"
    POST_URL = "https://www.reddit.com{permalink}.json"

    SORT_OPTIONS = ["relevance", "new", "top", "comments"]
    TIME_OPTIONS = ["hour", "day", "week", "month", "year", "all"]

    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self._last_request = 0.0

    async def _rate_limit(self):
        """Enforce delay between requests."""
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        self._last_request = time.time()

    @retry(
        max_retries=3,
        initial_backoff=2.0,
        backoff_factor=2.0,
        retry_on=(httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException),
    )
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search Reddit posts by query.

        Args:
            query: Search term (can include subreddit filters)
            limit: Max results to return

        Returns:
            List of SearchResult with post title, URL, and snippet
        """
        await self._rate_limit()

        headers = {"User-Agent": USER_AGENT}
        params = {"q": query, "limit": min(limit, 100), "sort": "relevance"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL, headers=headers, params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for post in data.get("data", {}).get("children", []):
            if len(results) >= limit:
                break

            d = post.get("data", {})
            if d.get("over_18"):
                continue

            title = d.get("title", "")
            permalink = d.get("permalink", "")
            selftext = d.get("selftext", "")
            url = d.get("url", "")

            reddit_url = f"https://www.reddit.com{permalink}" if permalink else url
            snippet = selftext[:200] if selftext else d.get("link_flair_text", "")

            results.append(
                SearchResult(
                    title=title,
                    url=reddit_url,
                    snippet=snippet,
                )
            )

        return results

    async def search_subreddit(
        self,
        subreddit: str,
        query: str = "",
        sort: str = "hot",
        time_filter: str = "month",
        limit: int = 25,
    ) -> list[dict]:
        """Search within a specific subreddit.

        Args:
            subreddit: Subreddit name (without r/)
            query: Search query within subreddit (empty for top posts)
            sort: Sort order (hot, new, top, rising)
            time_filter: Time filter (hour, day, week, month, year, all)
            limit: Max results

        Returns:
            List of post dicts with full metadata
        """
        await self._rate_limit()

        headers = {"User-Agent": USER_AGENT}

        if query:
            url = self.BASE_URL
            params = {
                "q": f"{query} subreddit:{subreddit}",
                "limit": min(limit, 100),
                "sort": sort if sort != "hot" else "relevance",
                "t": time_filter,
            }
        else:
            url = self.SUBREDDIT_URL.format(subreddit=subreddit, sort=sort)
            params = {"limit": min(limit, 100), "t": time_filter}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=headers, params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        posts = []
        for post in data.get("data", {}).get("children", []):
            if len(posts) >= limit:
                break

            d = post.get("data", {})
            if d.get("over_18"):
                continue

            posts.append(
                {
                    "id": d.get("id"),
                    "title": d.get("title", ""),
                    "author": d.get("author", ""),
                    "subreddit": d.get("subreddit", ""),
                    "selftext": d.get("selftext", ""),
                    "url": d.get("url", ""),
                    "permalink": f"https://www.reddit.com{d.get('permalink', '')}",
                    "score": d.get("score", 0),
                    "num_comments": d.get("num_comments", 0),
                    "created_utc": d.get("created_utc", 0),
                    "link_flair_text": d.get("link_flair_text", ""),
                    "is_self": d.get("is_self", False),
                }
            )

        return posts

    async def get_post_details(self, permalink: str) -> dict | None:
        """Get full post details including comments.

        Args:
            permalink: Reddit permalink (e.g. /r/python/comments/abc123/title/)

        Returns:
            Dict with post and comment data, or None
        """
        await self._rate_limit()

        url = (
            f"https://www.reddit.com{permalink}.json"
            if not permalink.startswith("http")
            else f"{permalink}.json"
        )
        headers = {"User-Agent": USER_AGENT}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            if response.status_code != 200:
                return None
            data = response.json()

        if not data or len(data) < 2:
            return None

        post_data = data[0].get("data", {}).get("children", [{}])[0].get("data", {})
        comments_data = data[1].get("data", {}).get("children", [])

        return {
            "title": post_data.get("title", ""),
            "author": post_data.get("author", ""),
            "selftext": post_data.get("selftext", ""),
            "subreddit": post_data.get("subreddit", ""),
            "score": post_data.get("score", 0),
            "num_comments": post_data.get("num_comments", 0),
            "url": post_data.get("url", ""),
            "permalink": f"https://www.reddit.com{post_data.get('permalink', '')}",
            "comments": self._flatten_comments(comments_data),
        }

    def _flatten_comments(self, comments: list, depth: int = 0) -> list[dict]:
        """Flatten nested comment structure."""
        flat = []
        for comment in comments:
            d = comment.get("data", {})
            if d.get("author") == "[deleted]":
                continue
            flat.append(
                {
                    "author": d.get("author", ""),
                    "body": d.get("body", ""),
                    "score": d.get("score", 0),
                    "depth": depth,
                }
            )
            children = d.get("replies", {})
            if isinstance(children, dict):
                child_list = children.get("data", {}).get("children", [])
                flat.extend(self._flatten_comments(child_list, depth + 1))
        return flat

    def get_provider_name(self) -> str:
        return "reddit"
