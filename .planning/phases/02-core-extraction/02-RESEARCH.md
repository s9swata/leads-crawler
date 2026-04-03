# Phase 2: Core Extraction - Research

**Researched:** 2026-04-03
**Domain:** Web scraping, HTML parsing, contact data extraction (email, phone, social links)
**Confidence:** HIGH

## Summary

Phase 2 implements the core extraction pipeline: fetching web pages via Crawl4ai, parsing HTML with BeautifulSoup, and extracting contact data (emails, phones, social links) using regex patterns. The chosen stack leverages Crawl4ai's built-in JavaScript rendering (via Playwright) to handle dynamic content, and BeautifulSoup for robust HTML parsing. The Strategy pattern for source adapters enables multiple scraper implementations while maintaining a common interface.

**Primary recommendation:** Use Crawl4ai for HTTP/browser scraping with JavaScript rendering, BeautifulSoup4 for HTML parsing, custom regex extractors for contact data, and implement the source adapter interface using the Strategy pattern.

---

## User Constraints (from context)

*(No CONTEXT.md exists - using roadmap and Phase 1 decisions as constraints)*

### Locked Decisions (from ROADMAP.md & Phase 1)
- Stack: Python 3.10+, Click for CLI, Pydantic for config
- Crawl4ai for web scraping (already in stack)
- RateLimiter and RobotsTxtParser already implemented (Phase 1)
- Lead schema already defined with source, source_url fields
- Project uses Poetry for dependency management
- Deliverables: HTTP/browser scraper (Crawl4ai), HTML parser (BeautifulSoup), email/phone/social extractors, Source adapter interface (Strategy pattern)

### Claude's Discretion
- Specific library choices for phone number extraction (regex vs phonenumbers library)
- Specific library for social link extraction (regex vs social-links library)
- Email extraction approach (custom regex vs extract-emails library)
- Whether to use Crawl4ai's built-in extraction or custom BeautifulSoup parsing

### Deferred Ideas (OUT OF SCOPE)
- LLM-based extraction (future phase)
- Company size/industry extraction (future work)

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Crawl4ai** | latest (0.8.x) | HTTP/browser scraper with JS rendering | Open source (63K+ stars), built-in Playwright, async-native, zero API costs |
| **BeautifulSoup4** | 4.x | HTML parsing | Python standard for HTML/XML parsing, robust with broken HTML |
| **Playwright** | (bundled with Crawl4ai) | Browser automation | Crawl4ai uses Playwright internally for JS rendering |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **phonenumbers** | 9.x | Phone number parsing/validation | When needing international phone number normalization |
| **social-links** | 1.x | Social media URL validation | When validating extracted social URLs |
| **lxml** | 5.x | Fast HTML parser for BeautifulSoup | When parsing large HTML documents |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Crawl4ai | Playwright direct, httpx+BeautifulSoup | Crawl4ai wraps Playwright with additional features (caching, extraction strategies) |
| BeautifulSoup | lxml directly, selectolax | BeautifulSoup is more robust with broken HTML; selectolax is faster but less forgiving |
| Custom regex | extract-emails library | Custom regex gives more control over extraction patterns |

---

## Architecture Patterns

### Recommended Project Structure

```
src/
├── cli/                    # CLI entry point (Phase 1)
├── config/                 # Configuration (Phase 1)
├── core/                   # Core types, rate limiter, robots (Phase 1)
├── extraction/            # NEW: Core extraction components
│   ├── __init__.py
│   ├── scraper.py         # Crawl4ai wrapper
│   ├── parser.py          # BeautifulSoup HTML parser
│   ├── extractors/        # Contact extraction modules
│   │   ├── __init__.py
│   │   ├── email.py       # Email extractor
│   │   ├── phone.py       # Phone number extractor
│   │   └── social.py      # Social link extractor
│   └── adapters/          # Source adapter interface (Strategy pattern)
│       ├── __init__.py
│       └── base.py        # Base adapter class
├── storage/                # Lead storage (Phase 1)
└── main.py               # CLI entry point
```

### Pattern 1: Crawl4ai Async Crawling

```python
# Source: https://docs.crawl4ai.com/core/browser-crawler-config
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def crawl_url(url: str):
    browser_conf = BrowserConfig(
        headless=True,
        browser_type="chromium"
    )
    
    run_conf = CrawlerRunConfig(
        wait_until="networkidle",
        page_timeout=30000
    )
    
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(url=url, config=run_conf)
        if result.success:
            return result.html, result.markdown
        return None, None
```

### Pattern 2: BeautifulSoup HTML Parsing

```python
# Source: https://realpython.com/python-web-scraping-bevel-soup/
from bs4 import BeautifulSoup

def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, 'lxml')

def extract_text(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return element.get_text(strip=True) if element else ""

def extract_links(soup: BeautifulSoup) -> list[str]:
    return [a.get('href') for a in soup.find_all('a', href=True)]
```

### Pattern 3: Email Extraction with Regex

```python
# Source: https://www.heybounce.io/email-validation-regex
import re

EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

def extract_emails(text: str) -> list[str]:
    emails = set(re.findall(EMAIL_PATTERN, text))
    return list(emails)

def extract_emails_from_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, 'lxml')
    text = soup.get_text(separator=' ')
    return extract_emails(text)
```

### Pattern 4: Phone Number Extraction

```python
# Source: https://daviddrysdale.github.io/python-phonenumbers/
import re
from phonenumbers import PhoneNumberMatcher

PHONE_PATTERNS = [
    r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US/International
    r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US formats
]

def extract_phones(text: str, region: str = None) -> list[str]:
    phones = []
    for pattern in PHONE_PATTERNS:
        phones.extend(re.findall(pattern, text))
    
    if region:
        for match in PhoneNumberMatcher(text, region):
            phones.append(match.raw_string)
    
    return list(set(phones))
```

### Pattern 5: Social Link Extraction

```python
# Source: https://github.com/lorey/social-media-profiles-regexs
import re

SOCIAL_PATTERNS = {
    'linkedin': r'linkedin\.com/(?:in|company|pub)/[a-zA-Z0-9_-]+',
    'twitter': r'(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+',
}

def extract_social_links(html: str) -> dict[str, list[str]]:
    soup = BeautifulSoup(html, 'lxml')
    links = [a.get('href') for a in soup.find_all('a', href=True)]
    
    results = {'linkedin': [], 'twitter': []}
    for platform, pattern in SOCIAL_PATTERNS.items():
        results[platform] = [link for link in links if re.search(pattern, link)]
    
    return results
```

### Pattern 6: Source Adapter (Strategy Pattern)

```python
# Source: Architecture research - Strategy pattern for sources
from abc import ABC, abstractmethod

class SourceAdapter(ABC):
    """Base class for source adapters (Strategy pattern)."""
    
    @abstractmethod
    async def fetch(self, url: str) -> str:
        """Fetch content from URL."""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the source identifier."""
        pass

class Crawl4aiAdapter(SourceAdapter):
    """Crawl4ai implementation of SourceAdapter."""
    
    def __init__(self, crawler: AsyncWebCrawler):
        self.crawler = crawler
    
    async def fetch(self, url: str) -> str:
        result = await self.crawler.arun(url)
        return result.html if result.success else None
    
    def get_source_name(self) -> str:
        return "crawl4ai"

class HttpsAdapter(SourceAdapter):
    """httpx implementation for simple HTTP requests."""
    
    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.text
    
    def get_source_name(self) -> str:
        return "httpx"
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| **Web scraping with JS** | Custom Playwright/Selenium setup | Crawl4ai | Built-in caching, extraction strategies, async-first, zero config |
| **HTML parsing** | Regex-based HTML parsing | BeautifulSoup | Handles broken HTML, multiple parsers, DOM traversal |
| **Email validation** | Custom email validator | Pydantic EmailStr + regex | Built-in validation, type safety |
| **JavaScript rendering** | Custom headless browser | Crawl4ai (Playwright) | Crawl4ai wraps Playwright with additional features |

**Key insight:** Crawl4ai handles both HTTP fetching and JavaScript rendering in one package. Use BeautifulSoup only for post-processing/parsing the returned HTML.

---

## Common Pitfalls

### Pitfall 1: Not Handling JavaScript-Rendered Content
**What goes wrong:** Extracted data is incomplete; dynamic content not captured
**Why it happens:** Using httpx/requests which don't execute JavaScript
**How to avoid:** Use Crawl4ai with headless browser (default) for dynamic content
**Warning signs:** Empty or minimal HTML returned, content loaded via AJAX not present

### Pitfall 2: Extracting Emails from Script Tags
**What goes wrong:** Getting obfuscated/spam emails, duplicates
**Why it happens:** Not filtering out JavaScript variables, email in `<script>` tags
**How to avoid:** Parse visible HTML only, filter by tag type, deduplicate results
**Warning signs:** Large number of similar emails, malformed addresses

### Pitfall 3: Phone Number Regex Too Broad
**What goes wrong:** Extracting random numbers (dates, IDs) as phone numbers
**Why it happens:** Overly permissive regex patterns
**How to avoid:** Use context-aware extraction (look near "tel:", "phone", "+1" prefixes)
**Warning signs:** High false positive rate, numbers in unexpected formats

### Pitfall 4: Not Respecting Rate Limits During Extraction
**What goes wrong:** Getting blocked by target sites
**Why it happens:** Extracting too fast from same domain
**How to avoid:** Integrate Phase 1's RateLimiter into extraction; respect per-domain delays
**Warning signs:** 403/429 errors, connection timeouts

### Pitfall 5: Social Links Without Validation
**What goes wrong:** Invalid/outdated social links exported as valid
**Why it happens:** Not validating extracted URLs match expected patterns
**How to avoid:** Use regex validation, optionally use social-links library for validation
**Warning signs:** Links don't open, redirect to 404 pages

---

## Code Examples

### Complete Extraction Pipeline

```python
# src/extraction/scraper.py
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

class Scraper:
    """Web scraper using Crawl4ai."""
    
    def __init__(self):
        self.browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            text_mode=True  # Faster for text extraction
        )
        self.crawler = None
    
    async def __aenter__(self):
        self.crawler = AsyncWebCrawler(config=self.browser_config)
        await self.crawler.__aenter__()
        return self
    
    async def __aexit__(self, *args):
        if self.crawler:
            await self.crawler.__aexit__(*args)
    
    async def fetch(self, url: str) -> str:
        result = await self.crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                wait_until="networkidle",
                page_timeout=30000,
                scan_full_page=True
            )
        )
        return result.html if result.success else None
```

```python
# src/extraction/extractors/email.py
import re

class EmailExtractor:
    """Extracts email addresses from HTML or text."""
    
    PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    ]
    
    def extract_from_text(self, text: str) -> list[str]:
        emails = set()
        for pattern in self.PATTERNS:
            matches = re.findall(pattern, text)
            emails.update(matches)
        return list(emails)
    
    def extract_from_html(self, html: str) -> list[str]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        # Get visible text
        text = soup.get_text(separator=' ')
        return self.extract_from_text(text)
```

```python
# src/extraction/extractors/phone.py
import re
from typing import Optional

class PhoneExtractor:
    """Extracts phone numbers from HTML or text."""
    
    PATTERNS = [
        r'\+?1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US
        r'\+?\d{1,4[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
    ]
    
    def extract_from_text(self, text: str) -> list[str]:
        phones = set()
        for pattern in self.PATTERNS:
            matches = re.findall(pattern, text)
            phones.update(self._normalize(phone) for phone in matches)
        return list(phones)
    
    def _normalize(self, phone: str) -> str:
        return ''.join(c for c in phone if c.isdigit() or c == '+')
    
    def extract_from_html(self, html: str) -> list[str]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # Check for tel: links
        phones = []
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('tel:'):
                phones.append(a['href'][4:])
        
        # Also check text content
        text = soup.get_text(separator=' ')
        phones.extend(self.extract_from_text(text))
        
        return list(set(phones))
```

```python
# src/extraction/extractors/social.py
import re
from typing import Optional

class SocialExtractor:
    """Extracts LinkedIn and Twitter/X links from HTML."""
    
    LINKEDIN_PATTERN = r'linkedin\.com/(?:in|company|pub)/[a-zA-Z0-9_-]+'
    TWITTER_PATTERN = r'(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+'
    
    def extract_from_html(self, html: str) -> dict[str, list[str]]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        linkedin = [self._normalize_url(link) for link in links 
                    if re.search(self.LINKEDIN_PATTERN, link)]
        
        twitter = [self._normalize_url(link) for link in links 
                   if re.search(self.TWITTER_PATTERN, link)]
        
        return {'linkedin': linkedin, 'twitter': twitter}
    
    def _normalize_url(self, url: str) -> str:
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return 'https://linkedin.com' + url  # Would need base URL
        return url
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| requests + BeautifulSoup | Crawl4ai (Playwright) | 2024+ | JavaScript rendering built-in |
| Manual regex parsing | BeautifulSoup + regex | Pre-2020 | Cleaner DOM traversal |
| Custom scraper classes | Source Adapter (Strategy pattern) | 2023+ | Swappable implementations |
| httpx only | Crawl4ai for browser, httpx for simple | 2024+ | Dynamic content support |

**Deprecated/outdated:**
- **urllib.request**: Use httpx or Crawl4ai
- **Selenium**: Use Crawl4ai (wraps Playwright, more features)
- **Scrapy**: Use for large-scale crawling; Crawl4ai better for individual site extraction

---

## Open Questions

1. **Should we use Crawl4ai's built-in extraction or custom BeautifulSoup parsing?**
   - What we know: Crawl4ai has JsonCssExtractionStrategy and LLM-based extraction
   - What's unclear: Performance comparison for simple contact extraction
   - Recommendation: Use BeautifulSoup for now (more control), evaluate Crawl4ai extraction later

2. **Should phone extraction use the phonenumbers library for validation?**
   - What we know: phonenumbers provides international parsing and validation
   - What's unclear: Additional dependency overhead vs accuracy gain
   - Recommendation: Start with regex, add phonenumbers if international support needed

3. **Should we use the social-links library for URL validation?**
   - What we know: social-links validates 65+ platforms, includes URL normalization
   - What's unclear: Overkill for just LinkedIn/Twitter, additional dependency
   - Recommendation: Use custom regex first (fewer deps), evaluate social-links later if needed

4. **How to handle JavaScript-rendered pages requiring user interaction?**
   - What we know: Crawl4ai supports js_code, wait_for, scan_full_page
   - What's unclear: Best approach for "load more" buttons, infinite scroll
   - Recommendation: Start with scan_full_page, add js_code for specific sites as needed

---

## Sources

### Primary (HIGH confidence)
- [Crawl4AI Documentation - Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config) - Official docs, v0.8.x
- [Crawl4AI Documentation - AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler) - Official docs
- [Real Python - Beautiful Soup Web Scraper](https://realpython.com/beautiful-soup-web-scraper-python/) - Verified tutorial

### Secondary (MEDIUM confidence)
- [WebSearch: Email Validation Regex 2025](https://www.heybounce.io/email-validation-regex) - Current patterns
- [GitHub - social-media-profiles-regexs](https://github.com/lorey/social-media-profiles-regexs) - Community patterns, 645 stars
- [phonenumbers Python library](https://pypi.org/project/phonenumbers/) - Google lib port, stable

### Tertiary (LOW confidence)
- [Project research files](.planning/research/) - Phase 1 research, needs verification

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Crawl4ai, BeautifulSoup are well-documented with stable APIs
- Architecture: HIGH - Based on project roadmap and Phase 1 decisions
- Pitfalls: MEDIUM - Known patterns but extraction specifics depend on test sites

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (30 days - stable libraries)