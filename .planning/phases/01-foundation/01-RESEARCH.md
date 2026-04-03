# Phase 1: Foundation - Research

**Researched:** 2026-04-03
**Domain:** CLI scaffold, configuration management, rate limiting, lead schema
**Confidence:** HIGH

## Summary

Phase 1 establishes the foundational infrastructure: CLI entry point, configuration management, rate limiting framework, robots.txt compliance, and lead data schema. The chosen stack (Python 3.11+, Click, Pydantic Settings, protego) is well-established with excellent documentation. Key insight: Crawl4ai has built-in robots.txt support via `respect_robots_txt_file=True`, so we can leverage that rather than building custom parsing.

**Primary recommendation:** Use Click for CLI, Pydantic Settings for config (env + YAML/JSON), asyncio-based rate limiting with crawl-delay parsing, and Pydantic for lead schema validation.

---

## User Constraints (from context)

*(No CONTEXT.md exists - using roadmap decisions as constraints)*

### Locked Decisions (from ROADMAP.md)
- CLI entry point with Click framework
- Config loader (.env, YAML, JSON support)
- Rate limiter with crawl-delay respect
- robots.txt parser
- Lead schema with validation
- Stack: Python 3.11+, Click for CLI, Crawl4ai for scraping, Serper.dev for search

### Claude's Discretion
- Specific library choices for rate limiting (asyncio.sleep vs aiolimiter vs throttled-py)
- robots.txt parser implementation (protego vs custom vs Crawl4ai built-in)

### Deferred Ideas
- None specified for Phase 1

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Python** | 3.11+ | Primary language | Rich async ecosystem, mature scraping libraries |
| **Click** | 8.x | CLI framework | Pallets project, Python standard for CLI |
| **Pydantic** | 2.x | Data validation | Fast, type-safe validation |
| **pydantic-settings** | 2.x | Config management | Loads from env, .env, YAML, JSON with validation |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **python-dotenv** | 1.0+ | .env file loading | Pydantic Settings uses it automatically |
| **PyYAML** | 6.0+ | YAML config parsing | When using YAML config files |
| **protego** | latest | robots.txt parsing | When building custom robots.txt handling |
| **tqdm** | 4.66+ | Progress bars | CLI progress display |

### Crawl4ai Built-in (already in stack)

| Feature | Implementation | Notes |
|---------|----------------|-------|
| **robots.txt** | `respect_robots_txt_file=True` | Built-in, parses crawl-delay |
| **Rate limiting** | `max_concurrent_requests`, `page_timeout` | Crawl4ai handles internally |

---

## Architecture Patterns

### Recommended Project Structure

```
src/
├── cli/                    # CLI entry point
│   ├── __init__.py        # Click group definition
│   └── commands/         # Subcommands (search, scrape, export, view)
├── config/                # Configuration management
│   ├── __init__.py       # Config loader
│   └── settings.py       # Pydantic Settings class
├── core/                  # Core business logic
│   ├── rate_limiter.py   # Rate limiting with crawl-delay
│   ├── robots.py         # robots.txt parser wrapper
│   └── types.py          # Lead schema definition
├── storage/               # Data persistence
│   └── lead_store.py     # Lead storage
└── main.py               # CLI entry point
```

### Pattern 1: Click CLI with Options

```python
# Source: https://click.palletsprojects.com/en/stable/quickstart/
import click

@click.command()
@click.option('--config', type=click.Path(exists=True), help='Config file path')
@click.option('--rate-limit', default=10, help='Max requests per second')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def search(config, rate_limit, verbose):
    """Search for leads based on keyword and location."""
    click.echo(f'Rate limit: {rate_limit} req/s')
    if verbose:
        click.echo('Verbose mode enabled')

if __name__ == '__main__':
    search()
```

### Pattern 2: Pydantic Settings with Multiple Config Sources

```python
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'  # Allow additional config files
    )
    
    # API Configuration
    serper_api_key: str = ""
    crawl4ai_timeout: int = 30
    
    # Rate Limiting
    requests_per_second: float = 10.0
    respect_crawl_delay: bool = True
    
    # Output
    output_format: str = "csv"

settings = Settings()
```

### Pattern 3: Crawl4ai with robots.txt Respect

```python
# Source: https://crawlee.dev/python/docs/examples/respect-robots-txt-file
from crawlee.crawlers import BeautifulSoupCrawler

crawler = BeautifulSoupCrawler(
    respect_robots_txt_file=True  # Parses crawl-delay automatically
)

@crawler.router.default_handler
async def handle_page(context):
    # Crawl4ai respects crawl-delay from robots.txt
    pass
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| **CLI argument parsing** | argparse with manual validation | Click | Click provides decorators, help generation, subcommands |
| **Configuration validation** | Manual dict validation | Pydantic Settings | Type coercion, env var support, validation errors |
| **robots.txt parsing** | Custom regex parser | protego or Crawl4ai | Handles edge cases, User-Agent matching, cache directives |
| **Rate limiting** | Basic time.sleep | asyncio + Crawl4ai | Async-native, crawl-delay respect built-in |

**Key insight:** Crawl4ai already handles robots.txt and provides rate limiting. Phase 1 should wrap this functionality rather than reimplement it.

---

## Common Pitfalls

### Pitfall 1: Configuration Scope Blindness
**What goes wrong:** Hardcoding config paths, not supporting multiple sources (.env, YAML, JSON)
**Why it happens:** Assuming single config source, not checking pydantic-settings capabilities
**How to avoid:** Use Pydantic Settings with `env_file`, support multiple file formats via custom loader
**Warning signs:** "works on my machine" config failures

### Pitfall 2: robots.txt Not Respected
**What goes wrong:** Crawler gets blocked, IP banned, or blocked by sites
**Why it happens:** Ignoring crawl-delay directives, not checking disallow rules
**How to avoid:** Enable Crawl4ai's built-in `respect_robots_txt_file=True`, log compliance decisions
**Warning signs:** High failure rate, 403/429 errors

### Pitfall 3: Rate Limiting Too Aggressive
**What goes wrong:** Gets blocked by target sites despite robots.txt compliance
**Why it happens:** Not respecting crawl-delay, running too many concurrent requests
**How to avoid:** Configure Crawl4ai's `max_concurrent_requests=1`, respect per-domain crawl-delay
**Warning signs:** Intermittent 429 errors, connection timeouts

### Pitfall 4: CLI Help Not Comprehensive
**What goes wrong:** Users don't know available options, can't figure out how to configure
**Why it happens:** Skipping help documentation, not providing examples
**How to avoid:** Use Click's `@click.option(help=...)`, add `--help` examples
**Warning signs:** Users asking basic usage questions

---

## Code Examples

### CLI Entry Point with Click

```python
# src/main.py
import click
from .config.settings import Settings
from .core.rate_limiter import RateLimiter
from .core.robots import RobotsTxtParser
from .core.types import LeadSchema

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Lead Generation CLI - Find and extract business contact information."""
    pass

@cli.command()
@click.argument('query')
@click.option('--location', default='', help='Location to search in')
@click.option('--limit', default=10, help='Maximum number of leads')
@click.option('--config', type=click.Path(exists=True), help='Config file path')
def search(query, location, limit, config):
    """Search for leads matching QUERY."""
    settings = Settings(config_path=config)
    click.echo(f'Searching for: {query} in {location or "all locations"}')
    # Implementation...

@cli.command()
def init():
    """Initialize configuration file."""
    # Create .env.example or default config
    pass

if __name__ == '__main__':
    cli()
```

### Configuration Loader

```python
# src/config/settings.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    serper_api_key: str = Field(default="", description="Serper.dev API key")
    max_requests_per_second: float = Field(default=10.0, description="Rate limit")
    respect_robots_txt: bool = Field(default=True, description="Respect robots.txt")
    output_dir: str = Field(default="./output", description="Output directory")
    
    @classmethod
    def from_file(cls, path: str):
        """Load from YAML or JSON config file."""
        with open(path) as f:
            if path.endswith('.yaml') or path.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        return cls(**data)
```

### Lead Schema with Validation

```python
# src/core/types.py
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class LeadSchema(BaseModel):
    """Lead data schema with validation."""
    
    id: str = Field(..., description="Unique lead identifier")
    company_name: str = Field(..., min_length=1, max_length=500)
    website: Optional[str] = Field(default=None, description="Company website URL")
    email: Optional[EmailStr] = Field(default=None, description="Contact email")
    phone: Optional[str] = Field(default=None, description="Phone number")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn URL")
    source: str = Field(..., description="Source of lead (search/discovery)")
    source_url: str = Field(..., description="URL where lead was discovered")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    scraped_at: Optional[datetime] = Field(default=None)
    
    @field_validator('website', 'linkedin')
    @classmethod
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v
    
    @field_validator('phone')
    @classmethod
    def normalize_phone(cls, v):
        if v:
            return ''.join(c for c in v if c.isdigit() or c == '+')
        return v
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| argparse | Click | Pre-2020 | Click provides decorators, nested commands, better help |
| Manual config dicts | Pydantic Settings | 2020+ | Type coercion, validation, env var support |
| Custom robots.txt | Crawl4ai built-in | 2024+ | Zero-config compliance, crawl-delay parsing |
| time.sleep() | asyncio | 2020+ | Non-blocking, essential for async crawlers |

**Deprecated/outdated:**
- **urllib.request**: Use httpx or curl_cffi for async HTTP
- **dict-based config**: Use Pydantic Settings for validation
- **Manual rate limiting**: Use Crawl4ai's built-in throttling

---

## Open Questions

1. **Should we use Crawl4ai's built-in robots.txt or implement custom?**
   - What we know: Crawl4ai has `respect_robots_txt_file=True` that parses crawl-delay
   - What's unclear: How granular is the control? Can we log specific decisions?
   - Recommendation: Use Crawl4ai's built-in first, add custom wrapper only if needed

2. **How to handle multiple config file formats?**
   - What we know: Pydantic Settings supports env vars natively, YAML/JSON via custom loaders
   - What's unclear: What's the priority order? .env vs config.yaml vs CLI flags?
   - Recommendation: CLI flags > config file > env vars > defaults (cascading)

3. **Should rate limiting be global or per-domain?**
   - What we know: Per-domain is more respectful but more complex to implement
   - What's unclear: Can Crawl4ai handle per-domain crawl-delay?
   - Recommendation: Start with global rate limit, add per-domain if needed

---

## Sources

### Primary (HIGH confidence)
- [Click Documentation](https://click.palletsprojects.com/) - Official docs, 8.3.x
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Official docs
- [Crawlee Python - Respect robots.txt](https://crawlee.dev/python/docs/examples/respect-robots-txt-file) - Official docs (Crawlee is Crawl4ai's core)

### Secondary (MEDIUM confidence)
- [WebSearch: Python CLI frameworks 2025](https://oneuptime.com/blog/post/2026-01-30-python-click-cli-applications/view) - Jan 2026
- [WebSearch: Python rate limiting libraries](https://github.com/ZhuoZhuoCrayon/throttled-py) - GitHub, 627 stars

### Tertiary (LOW confidence)
- [Stack research](.planning/research/STACK.md) - Project-specific research

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Click, Pydantic, Crawl4ai are well-documented with stable APIs
- Architecture: HIGH - Based on existing project research and Crawl4ai's design
- Pitfalls: MEDIUM - Known patterns, but Phase 1 specifics depend on implementation

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (30 days - stable libraries)
