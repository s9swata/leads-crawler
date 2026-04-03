# Stack Research

**Domain:** B2B Lead Generation CLI Tool
**Researched:** 2026-04-03
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Language

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.11+ | Primary language | Dominant for web scraping due to rich ecosystem, async support (asyncio), easier proxy/rate-limit handling. Crawl4ai is Python-native. |
| **Node.js/TypeScript** | 20 LTS | CLI framework | If preferring JS ecosystem, Commander.js is the standard CLI framework. TypeScript adds type safety. |

**Recommendation:** Choose **Python** for this project. The scraping libraries (Crawl4ai, Playwright, Scrapy) are Python-first, and the ecosystem for data extraction, email parsing, and CSV export is mature.

### Core Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Crawl4ai** | latest (Apache 2.0) | Web crawling & extraction | Open source (40K+ GitHub stars), zero API costs, full JavaScript rendering via Playwright, built-in LLM extraction, proxy support. Runs locally. |
| **Playwright** | 1.50+ | Browser automation | Best anti-detection of any browser tool. Use directly when Crawl4ai isn't sufficient. |

**Why Crawl4ai over Scrapy?** Scrapy is battle-tested for large-scale crawling, but Crawl4ai provides modern async, JavaScript rendering, LLM-powered extraction, and zero vendor lock-in. For lead gen where you're visiting individual business websites, Crawl4ai's browser rendering is essential.

### Search/API Integration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Serper.dev** | API v1 | Google Search results | 2,500 free searches/month. Fast, reliable, legitimate API access. No rate limit battles. |
| **httpx** | 0.27+ | HTTP client | Modern async HTTP with connection pooling, timeouts, retries. Drop-in for requests. |
| **curl_cffi** | 0.7+ | HTTP client | C-based curl bindings. Faster than httpx, built-in TLS fingerprinting for anti-bot evasion. |

**Why not scrape Google directly?** Google actively blocks scrapers with CAPTCHA, IP bans, and constantly changing HTML. SERP APIs handle this. Start with Serper's free tier.

### Data Processing

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **Pandas** | 2.2+ | DataFrames | Lead storage, deduplication, CSV export. `to_csv()` is production-ready. |
| **BeautifulSoup** | 4.12+ | HTML parsing | Quick parsing of static pages without full browser rendering. |
| **lxml** | 5.0+ | XML/HTML parser | Faster than html.parser. Use with BeautifulSoup. |
| **protego** | latest | robots.txt parsing | Modern Python robots.txt parser. Supports modern conventions. |

### CLI Framework

| Technology | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **Click** | 8.1+ | CLI interface | Python-native. Built-in help, option parsing, terminal styling. Standard for Python CLIs. |
| **Typer** | 0.13+ | CLI interface | Built on Click with type hints. Cleaner code for complex CLIs. |
| **argparse** | stdlib | CLI interface | When you want zero dependencies. Click/Typer preferred. |

### Rate Limiting & Respectful Scraping

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **asyncio.sleep** | stdlib | Basic rate limiting | Simple delays between requests. |
| **aiolimiter** | 1.1+ | Async rate limiting | Token bucket/fixed window for async operations. |
| **tenacity** | 8.3+ | Retry logic | Exponential backoff for failed requests. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **extract-emails** | 6.1+ | Email extraction | Dedicated email/LinkedIn profile extraction from URLs. |
| **email-validator** | 2.2+ | Email validation | Validate extracted emails. |
| **tqdm** | 4.66+ | Progress bars | CLI progress indication for long crawls. |
| **python-dotenv** | 1.0+ | Config management | API key storage, config files. |
| **rich** | 13.7+ | Terminal output | Tables, colored output, styled CLI. |

## Installation

```bash
# Core scraping
pip install crawl4ai playwright
playwright install chromium

# HTTP client (if using direct requests)
pip install httpx curl_cffi

# Data processing
pip install pandas lxml beautifulsoup4

# Robots.txt
pip install protego

# CLI
pip install click typer rich

# Rate limiting & utilities
pip install tenacity aiolimiter email-validator tqdm python-dotenv

# Email extraction
pip install extract-emails

# Optional: LLM extraction (if using AI-powered extraction)
pip install openai anthropic
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|------------------------|
| Crawl4ai | Scrapy | When crawling thousands of static pages at scale without JS rendering needed. Scrapy has more battle-tested middleware. |
| Crawl4ai | Firecrawl | When you prefer managed API over self-hosted. Firecrawl costs per credit; Crawl4ai is free. |
| Serper.dev | SerpAPI | When you need more search engines (15+) or deeper SERP data. SerpAPI starts at $25/mo. |
| Serper.dev | Direct scraping | When you have proxies and want zero API costs. High maintenance, blocks likely. |
| Playwright | Selenium | When you need cross-browser testing or legacy support. Playwright is faster and more reliable. |
| Click | argparse | When building minimal CLI with no dependencies. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Selenium WebDriver** | Slow, easily detected, requires browser installation. | Playwright or Crawl4ai |
| **urllib/requests** (for scraping) | No async, no built-in retries, easy to block. | httpx or curl_cffi |
| **Scrapy for small-scale** | Steep learning curve, Twisted async (not asyncio), overkill for <100 pages. | BeautifulSoup + httpx |
| **Direct Google scraping** | Constant blocks, CAPTCHA, IP bans. Legal gray area. | Serper.dev or SerpAPI |
| **Bright Data** | Enterprise pricing ($500+/mo). Unless you have budget and need 72M proxies. | Crawl4ai + residential proxies |
| **Cheerio** | Node.js only. Use if staying in JS ecosystem. | BeautifulSoup (Python) |
| **Puppeteer** | Node.js only. Use Playwright instead (cross-browser, better API). | Playwright |

## Stack Patterns by Variant

**If targeting small-scale lead gen (<100 leads/day):**
- Serper.dev free tier + BeautifulSoup + CSV export
- Minimal infrastructure, no proxies needed
- Lower complexity, faster to build

**If targeting medium-scale (<1000 leads/day):**
- Serper.dev paid + Crawl4ai with Playwright
- Rotating proxies recommended
- Pandas for deduplication

**If targeting large-scale (1000+ leads/day):**
- Multiple SERP API providers for redundancy
- Scrapy for crawling efficiency + Playwright for JS sites
- Consider Apify actors for specific site scrapers
- Database storage (SQLite → PostgreSQL as needed)

## Version Compatibility

| Package | Compatible With | Notes |
|---------|----------------|-------|
| Python | 3.11+ | Use 3.12 for best async performance |
| Crawl4ai | Python 3.9+ | Requires Chromium (auto-installed) |
| Playwright | Python 3.8+ | Match with Crawl4ai requirements |
| Pandas | Python 3.9+ | 2.x has PyArrow backend for speed |
| httpx | Python 3.8+ | Async-first |

## Sources

- [Scrapy vs Playwright vs Crawlee (DEV Community, Mar 2026)](https://dev.to/0012303/scrapy-vs-playwright-vs-crawlee-which-web-scraping-tool-should-you-use-in-2026-1eik) — MEDIUM confidence
- [Crawl4ai Guide (DataResearchTools, Mar 2026)](https://dataresearchtools.com/crawl4ai-guide/) — HIGH confidence
- [Best CLI Frameworks for Node.js 2026 (PkgPulse, Mar 2026)](https://www.pkgpulse.com/blog/best-cli-frameworks-nodejs-2026) — MEDIUM confidence
- [Best Node.js Web Scrapers 2026 (ScrapingBee, Feb 2026)](https://www.scrapingbee.com/blog/best-node-js-web-scrapers/) — MEDIUM confidence
- [Google Search API Alternatives 2026 (Apiserpent)](https://apiserpent.com/blog/google-search-api-alternatives.html) — MEDIUM confidence
- [Serper Pricing](https://serp.ai/tools/serper/) — HIGH confidence (official)
- [Crawl4ai GitHub (40K+ stars)](https://github.com/unclecode/crawl4ai) — HIGH confidence (source)

---
*Stack research for: B2B Lead Generation CLI Tool*
*Researched: 2026-04-03*
