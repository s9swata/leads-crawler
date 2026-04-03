# Project Research Summary

**Project:** Lead Generation Tool
**Domain:** B2B Lead Generation CLI Tool for Web Development Agencies
**Researched:** 2026-04-03
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project is a CLI tool for web development agencies to automate lead generation by aggregating contact data from free sources (Google Search, public directories, business websites) and exporting to CSV for cold outreach. The core value is delivering actionable leads with verified contact info that sales teams can immediately use.

The recommended approach is Python-first with Crawl4ai for web crawling (40K+ GitHub stars, Apache 2.0, zero API costs), Serper.dev for Google search (2,500 free searches/month), and Click for CLI. This stack avoids vendor lock-in while providing modern async support and JavaScript rendering for modern websites.

Key risks include legal non-compliance (GDPR, robots.txt violations), unverified email data causing bounce rates, and aggressive rate limiting triggering blocks. These must be addressed in the foundation phase—legal compliance and data quality gates cannot be retrofitted.

## Key Findings

### Recommended Stack

Python is the clear choice for this project. The scraping ecosystem (Crawl4ai, Playwright, BeautifulSoup) is Python-native, and libraries for email parsing, data processing, and CSV export are mature. The stack prioritizes open-source tools with zero vendor lock-in: Crawl4ai handles browser rendering and LLM extraction, Serper.dev provides reliable Google search access without blocks, and Click delivers a clean CLI interface.

**Core technologies:**
- **Crawl4ai**: Web crawling & extraction — open source, zero API costs, full JavaScript rendering, built-in LLM extraction, proxy support
- **Serper.dev**: Google Search API — 2,500 free searches/month, fast and reliable, no rate limit battles
- **Click**: CLI framework — Python-native, built-in help, option parsing, terminal styling
- **Playwright**: Browser automation — best anti-detection, use when Crawl4ai isn't sufficient
- **Pandas**: DataFrames — lead storage, deduplication, CSV export with `to_csv()` production-ready
- **asyncio + aiolimiter + tenacity**: Async rate limiting and retry logic — essential for respectful scraping

### Expected Features

**Must have (table stakes):**
- CSV Import/Export — users already have spreadsheets; fundamental I/O
- Website/URL Scraping — core value prop; extracting business contact info
- Email Collection — primary deliverable for cold outreach
- Lead Deduplication — prevents waste from multiple sources
- Rate Limiting — essential to avoid IP blocks

**Should have (competitive):**
- Social Media Link Extraction — LinkedIn/Twitter profiles add credibility signals
- Phone Number Extraction — secondary contact method for multi-channel outreach
- Multi-Client Workspaces — agencies manage multiple clients; isolate each client's leads
- Batch Processing with Progress — agencies can't babysit long scrapes
- Basic Filtering — narrow down by location/industry

**Defer (v2+):**
- AI-Powered Enrichment Chat — requires LLM integration
- ICP Scoring — needs training data and scoring model
- MCP Server — niche use case for AI-forward users
- Tech Stack Detection — useful but complex (BuiltWith-style analysis)
- Funding Stage Detection — requires Crunchbase integration

### Architecture Approach

The tool follows a **pipeline architecture** with four distinct layers: CLI Interface (parsing, config, output), Orchestration (source discovery, query management), Extraction (HTTP/browser scraping, HTML parsing, contact extraction), and Storage (raw cache, lead store, deduplication). The Strategy pattern enables multiple search sources (Google, directories, websites) with a common interface.

**Major components:**
1. **CLI Parser & Config** — argument parsing, API key management, source configurations
2. **Source Manager** — discovers URLs via search, manages search queries (Strategy pattern)
3. **Scraper + Parser + Contact Extractor** — fetches, parses HTML, extracts emails/phones/social links
4. **Lead Store + Deduplication** — normalizes, persists, prevents duplicates by domain/email

### Critical Pitfalls

1. **Legal Non-Compliance** — scraping restricted sites causes IP bans, cease-and-desist, GDPR fines. Must parse robots.txt, check ToS, add legal warnings, never scrape EU personal data without lawful basis.

2. **Unverified Email Data** — pattern-guessed emails bounce, destroying sender reputation. Integrate SMTP verification, flag catch-all domains, only export verified emails, implement confidence scoring.

3. **Aggressive Rate Limiting Violations** — IP gets blocked, tool becomes unusable. Respect crawl-delay directives, implement exponential backoff on 429s, rotate user-agents, set conservative defaults.

4. **Poor Data Quality** — incomplete/wrong format leads waste user time. Define strict schema, validate at extraction time, flag leads with missing required fields, never export below quality threshold.

5. **Hardcoded API Keys** — credentials exposed in repo. Use dotenv with .env.example committed, load secrets from environment at runtime.

## Implications for Roadmap

Based on research, the natural phase structure prioritizes foundation work that cannot be retrofitted:

### Phase 1: Foundation
**Rationale:** Legal compliance, rate limiting, and data quality gates must be built from day one—they cannot be added later without rewriting core logic.
**Delivers:** CLI scaffold, config management, robots.txt parsing, rate limiting framework, lead schema with validation
**Addresses:** P1 features (CSV I/O, deduplication), all critical pitfalls (legal, email verification, rate limits)
**Avoids:** Retrofitting legal compliance, hardcoded credentials

### Phase 2: Core Extraction
**Rationale:** Web scraping and contact extraction are the primary value deliverable. Build these once the foundation (rate limiting, config) is in place.
**Delivers:** HTTP/browser scraper, HTML parser, email/phone/social extractor, source adapter framework
**Addresses:** P1 features (website scraping, email collection)
**Uses:** Crawl4ai, Playwright, BeautifulSoup, extract-emails

### Phase 3: Persistence & Export
**Rationale:** Leads need to be stored between runs, deduplicated, and exported. Storage abstraction enables future database migrations.
**Delivers:** Lead store (SQLite/JSON), deduplication engine, CSV generator with column mapping
**Implements:** Repository pattern for data access abstraction

### Phase 4: Multi-Source & Search
**Rationale:** Multiple sources (Google search, directories, direct website) scale the tool. Source Strategy pattern makes this additive, not a rewrite.
**Delivers:** Serper.dev integration, directory source adapters, website source adapter
**Implements:** Strategy pattern for interchangeable sources

### Phase 5: Resilience & Polish
**Rationale:** Production reliability—retry logic, caching, progress reporting, error recovery. This is what separates a prototype from a tool users trust.
**Delivers:** Checkpoint/resume system, retry with exponential backoff, progress bars, dry-run mode
**Avoids:** Lost progress on failure, cryptic errors, silent failures

### Phase Ordering Rationale

- **Foundation first:** Legal compliance and rate limiting cannot be retrofitted; they must be architectural foundations
- **Core extraction second:** Scraping is the primary value—build on foundation, not before it
- **Persistence before multi-source:** Storage abstraction enables clean source additions later
- **Resilience last:** Progressive enhancement after core loop works; don't add complexity before validating the basic flow

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Core Extraction):** Complex integration—needs selector strategy research per source type
- **Phase 4 (Multi-Source):** Niche domain—directory scraping patterns vary widely; may need per-directory research

Phases with standard patterns (skip research-phase):
- **Phase 1:** Well-documented patterns (robots.txt parsing, rate limiting, CLI scaffolding)
- **Phase 3:** SQLite/JSON storage is standard; CSV export is mature

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified with Crawl4ai GitHub (40K+ stars), official docs, community benchmarks |
| Features | MEDIUM | Community consensus on table stakes; differentiators inferred from competitor analysis |
| Architecture | MEDIUM-HIGH | Based on Crawlee/Crawlee architecture patterns; standard pipeline design |
| Pitfalls | MEDIUM-HIGH | Based on industry reports, GDPR case studies, scraping community patterns |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Email verification approach:** Research recommends SMTP verification but MVP cost/complexity trade-off unclear. During planning: decide between free tier tools (ZeroBounce trial, AbstractAPI) or accept higher bounce risk for launch.
- **ICP scoring methodology:** Nice-to-have v2 feature but scoring criteria (budget, timeline, fit) need validation with actual agency users. During planning: interview beta users on what makes a "good" lead for them.

## Sources

### Primary (HIGH confidence)
- [Crawl4ai GitHub (40K+ stars)](https://github.com/unclecode/crawl4ai) — Stack recommendation, technical specs
- [Serper Pricing](https://serp.ai/tools/serper/) — API limits, free tier details
- [Crawlee Architecture Overview](https://crawlee.dev/python/docs/guides/architecture-overview) — Pipeline patterns
- [Web Scraping Architecture Patterns: From Prototype to Production](https://use-apify.com/blog/web-scraping-architecture-patterns) — Build order

### Secondary (MEDIUM confidence)
- [Scrapy vs Playwright vs Crawlee (DEV Community, Mar 2026)](https://dev.to/0012303/scrapy-vs-playwright-vs-crawlee-which-web-scraping-tool-should-you-use-in-2026-1eik) — Stack comparison
- [LeadMagic CLI](https://leadmagic.io/solutions/cli) — Feature landscape reference
- [ScrapeGraphAI: Common Web Scraping Mistakes](https://www.scrapegraphai.com/blog/common-errors) — Pitfall patterns

### Tertiary (LOW confidence)
- [Medium: Web Scraping GDPR €20M Mistake](https://medium.com/deep-tech-insights/web-scraping-in-2025-the-20-million-gdpr-mistake-you-cant-afford-to-make-07a3ce240f4f) — Legal compliance (needs legal counsel validation)
- [Instantly: Cold Email Software Mistakes](https://instantly.ai/blog/cold-email-software-mistakes-to-avoid-12-costly-errors-that-tank-deliverability-roi/) — Email deliverability patterns

---
*Research completed: 2026-04-03*
*Ready for roadmap: yes*
