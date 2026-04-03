# Phase 4: Search Discovery - Research

**Researched:** 2026-04-03  
**Domain:** Google search API for lead discovery (Serper.dev)  
**Confidence:** HIGH

## Summary

Serper.dev is a Google Search API that provides SERP results without scraping. It offers a simple REST API with JSON responses, making it ideal for lead discovery before scraping. The existing codebase already has `serper_api_key` configured in Settings, indicating this was a planned feature.

**Recommendation:** Implement Serper.dev as a simple HTTP client (httpx) rather than a heavy SDK. Create a search adapter that fits the existing SourceAdapter pattern, enabling the `search` command to return lead candidates for subsequent scraping.

---

## User Constraints

- Python 3.10+, Click CLI, Pydantic, Crawl4ai, SQLAlchemy
- Poetry for dependency management
- Already has `serper_api_key` in Settings (Phase 1/2 had this in mind)
- Uses Strategy pattern for source adapters
- RateLimiter already implemented (important for API rate limits)

---

## Serper.dev API Details

### API Endpoint
```
POST https://google.serper.dev/search
Headers: X-API-Key: <your-api-key>
Body: {"q": "search query", "num": 10}
```

### Key Features
- **Free tier:** Available with limits
- **Response format:** JSON with organic results, knowledge graph, ads
- **Parameters:** `q` (query), `num` (results, default 10), `location`, `gl` (country), `hl` (language)
- **Search types:** `/search` (web), `/images`, `/news`, `/shopping`, `/scholar`

### Response Structure
```json
{
  "searchParameters": {...},
  "organic": [
    {
      "title": "Result Title",
      "link": "https://example.com",
      "snippet": "Result description..."
    }
  ],
  "knowledgeGraph": {...}
}
```

---

## Python Integration

### Option 1: Direct HTTP (Recommended)
```python
import httpx
import os

class SerperClient:
    BASE_URL = "https://google.serper.dev/search"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
    
    def search(self, query: str, num: int = 10) -> list[dict]:
        headers = {"X-API-Key": self.api_key}
        data = {"q": query, "num": num}
        
        response = httpx.post(self.BASE_URL, headers=headers, json=data)
        response.raise_for_status()
        
        results = response.json()
        return results.get("organic", [])
```

### Option 2: crewai[tools] SerperDevTool
```python
from crewai_tools import SerperDevTool

tool = SerperDevTool(n_results=10)
results = tool.run(search_query="restaurants in New York")
```

**Tradeoff:** Option 1 has zero extra dependencies, more control. Option 2 brings additional tooling.

---

## Architecture Integration

### Existing Pattern to Follow

The project uses Strategy pattern for source adapters in `src/extraction/adapters/base.py`:

```python
class SourceAdapter(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> str: ...
    @abstractmethod
    def get_source_name(self) -> str: ...
```

For search, we need a different pattern - a **SearchAdapter** that returns URLs for leads:

```python
# src/search/adapters/serper_adapter.py
class SearchAdapter(ABC):
    """Abstract base for search providers."""
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        pass

# src/search/adapters/serper_adapter.py  
class SerperAdapter(SearchAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        # Implementation using httpx
        pass
```

### Integration with Existing CLI

The `search` command in `commands.py` already exists (stub):

```python
@click.command(name="search")
@click.option("--query", required=True, help="Search query for finding leads")
@click.option("--location", help="Location to search in")
@click.option("--limit", default=10, help="Maximum number of results")
def search(query, location, limit):
    """Search for business leads based on query and location."""
```

This needs to be implemented to:
1. Fetch search results from Serper.dev
2. Convert results to lead candidates (URL, title, snippet)
3. Optionally auto-ingest to database with source="search"

### Integration with LeadIngestionService

```python
# After getting search results, use existing LeadIngestionService
ingestion_service = LeadIngestionService()
leads = ingestion_service.ingest(
    data={
        "url": result["link"],
        "company_name": result["title"],  # Derived from title
    },
    source="search",
    source_url=result["link"],
)
```

---

## Rate Limiting Considerations

- **Serper.dev limits:** Check API tier for requests/minute
- **Implementation:** Use existing `RateLimiter` for API calls (per domain = serper.dev)
- **Built-in:** No additional rate limiting needed if under limits
- **Recommendation:** Add small delay between searches if batching

---

## Security Considerations

### API Key Handling

1. **Environment variable:** Already configured as `SERPER_API_KEY` in Settings
2. **Never commit:** Add to `.env.example` but not `.env`
3. **Settings integration:** Use existing pattern:
   ```python
   # src/config/settings.py already has:
   serper_api_key: Optional[str] = None
   ```

4. **CLI prompt:** If not set, prompt user or show helpful error:
   ```python
   if not settings.serper_api_key:
       raise click.ClickException(
           "SERPER_API_KEY not set. Get one at https://serper.dev/"
       )
   ```

### .env Example Template
```
# Get your free API key at https://serper.dev/
SERPER_API_KEY=your-api-key-here
```

---

## Dependencies Required

If using Option 1 (direct HTTP):
- **httpx** - Already in pyproject.toml ✓

If using Option 2 (crewai tools):
- **crewai[tools]** - Additional dependency

**Recommendation:** Use Option 1 (direct httpx) - fewer dependencies, more control, matches existing patterns.

---

## Implementation Plan

1. **Create search module:**
   ```
   src/
   └── search/
       ├── __init__.py
       ├── adapters/
       │   ├── __init__.py
       │   ├── base.py       # SearchAdapter ABC
       │   └── serper.py     # SerperAdapter implementation
       └── models.py         # SearchResult model
   ```

2. **Implement SerperAdapter** using httpx (already available)

3. **Update `commands.py` search command** to:
   - Read API key from settings
   - Call SerperAdapter.search()
   - Display results or ingest to database

4. **Add to pyproject.toml:** No new dependencies needed (httpx already there)

---

## Sources

- [Serper.dev Official](https://serper.dev/) - API provider
- [CrewAI SerperDevTool](https://docs.crewai.com/en/tools/search-research/serperdevtool) - Python usage example
- [LangChain Serper Integration](https://python.langchain.com/docs/integrations/providers/google_serper) - Alternative reference
- [GitHub - serpapi-python](https://github.com/serpapi/serpapi-python) - Alternative (paid) Python SDK

---

## Metadata

**Confidence breakdown:**
- API details: HIGH - Well-documented public API
- Architecture: HIGH - Follows existing patterns exactly
- Implementation: HIGH - Simple HTTP client, no complex logic

**Research date:** 2026-04-03  
**Valid until:** 2026-05-03 (30 days - stable API)