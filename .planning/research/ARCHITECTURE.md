# Architecture Research

**Domain:** Lead Generation CLI Tool
**Researched:** 2026-04-03
**Confidence:** MEDIUM-HIGH

## Standard Architecture

### System Overview

Lead generation CLI tools follow a **pipeline architecture** with clear separation between source discovery, data extraction, enrichment, and export. For a tool targeting web development agencies, the architecture spans 4 distinct layers.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI Interface Layer                           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  CLI Parser  │  │  Config Mgr  │  │  Output Formatter (CSV)  │ │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘ │
└─────────┼──────────────────┼────────────────────────┼────────────────┘
          │                  │                        │
┌─────────┼──────────────────┼────────────────────────┼────────────────┐
│         ▼                  ▼                        ▼                 │
│                     Orchestration Layer                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      Source Manager                           │  │
│  │   (discovers search sources, manages search queries)           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
├──────────────────────────────┼──────────────────────────────────────┤
│                              ▼                                      │
│                       Extraction Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │   Scraper    │  │   Parser     │  │  Contact Extractor   │    │
│  │  (HTTP/brow) │  │ (HTML→data) │  │ (email/phone/social) │    │
│  └──────────────┘  └──────────────┘  └──────────────────────┘    │
│                              │                                      │
├──────────────────────────────┼──────────────────────────────────────┤
│                              ▼                                      │
│                        Storage Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐       │
│  │  Raw Cache   │  │  Lead Store  │  │  Deduplication      │       │
│  │  (JSON/FS)   │  │  (structured)│  │  (by domain/email)  │       │
│  └──────────────┘  └──────────────┘  └──────────────────────┘       │
│                              │                                      │
├──────────────────────────────┼──────────────────────────────────────┤
│                              ▼                                      │
│                       Export Layer                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              CSV Generator (with column mapping)              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| CLI Parser | Argument parsing, command routing | Commander.js, yargs, oclif |
| Config Manager | API keys, defaults, source configs | dotenv + JSON config files |
| Source Manager | Defines where/how to search (Google, directories, etc.) | Strategy pattern per source |
| Scraper | Fetches HTML/content from URLs | HTTP client (got/axios) + optional Playwright |
| Parser | Extracts structured data from HTML/DOM | Cheerio, Puppeteer selectors |
| Contact Extractor | Regex/AI extraction of emails, phones, social links | Pattern matching + heuristics |
| Lead Store | Normalizes and persists leads between runs | JSON files or SQLite |
| Deduplication | Prevents duplicate leads by domain/email | Hash-based dedup |
| CSV Generator | Transforms leads to export format | csv-stringify |

## Recommended Project Structure

```
src/
├── cli/                    # CLI entry point and command definitions
│   ├── index.ts           # CLI bootstrap (commander/yargs setup)
│   ├── commands/         # Command handlers (search, export, etc.)
│   └── options/          # Shared CLI option definitions
├── config/                # Configuration loading and validation
│   ├── index.ts          # Config entry point
│   ├── schema.ts         # Zod validation schemas
│   └── sources.ts        # Source definitions (Google, directories, etc.)
├── core/                  # Core business logic
│   ├── orchestrator.ts   # Coordinates the scraping pipeline
│   ├── pipeline.ts       # Data flow orchestration
│   └── types.ts          # Shared types (Lead, Source, Result)
├── extractors/           # Data extraction modules
│   ├── scraper/         # HTTP and browser scraping
│   │   ├── http.ts      # HTTP client wrapper
│   │   ├── browser.ts   # Playwright/browser automation
│   │   └── index.ts     # Factory/selector
│   ├── parser/          # HTML/DOM parsing
│   │   ├── html.ts      # Cheerio-based parsing
│   │   └── selectors/   # Source-specific selectors
│   └── contacts/        # Contact info extraction
│       ├── email.ts     # Email regex/validation
│       ├── phone.ts     # Phone number extraction
│       └── social.ts    # Social link extraction
├── sources/              # Source adapters (Strategy pattern)
│   ├── base.ts          # Abstract source interface
│   ├── google.ts        # Google search scraping
│   ├── directory.ts     # Business directories
│   └── website.ts       # Direct website scraping
├── storage/              # Data persistence
│   ├── lead-store.ts    # Lead normalization and storage
│   ├── cache.ts         # Raw response cache
│   └── dedup.ts         # Deduplication logic
├── export/               # Export formatters
│   └── csv.ts           # CSV generation with column mapping
├── utils/                # Shared utilities
│   ├── rate-limit.ts    # Rate limiting
│   ├── retry.ts         # Retry logic
│   ├── logger.ts        # Structured logging
│   └── validate.ts      # Lead validation
└── index.ts             # Main export for programmatic use
```

### Structure Rationale

- **`cli/`:** Separates CLI-specific code from business logic, enabling programmatic use
- **`sources/`:** Strategy pattern allows adding new search sources without touching extraction logic
- **`extractors/`:** Modular scrapers allow swapping HTTP for browser based on target requirements
- **`storage/`:** Abstraction layer over persistence allows switching from JSON to SQLite later
- **`core/`:** Minimal orchestration code; most logic lives in focused modules

## Architectural Patterns

### Pattern 1: Pipeline (Chained Operations)

**What:** Data flows through a sequence of transformers, each adding or refining data.
**When to use:** Lead generation naturally follows a sequence: discover → scrape → extract → enrich → store → export.
**Trade-offs:** Simple to understand; sequential by nature; parallelization requires splitting at source level.

**Example:**
```typescript
async function runPipeline(sources: Source[], query: string): Promise<Lead[]> {
  const orchestrator = new PipelineOrchestrator();

  for (const source of sources) {
    const urls = await orchestrator.discover(source, query);
    const rawData = await orchestrator.scrape(urls);
    const extracted = await orchestrator.extract(rawData);
    const enriched = await orchestrator.enrich(extracted);
    await storage.save(enriched);
  }

  return storage.getAll();
}
```

### Pattern 2: Strategy (Source Adapters)

**What:** Interchangeable source implementations sharing a common interface.
**When to use:** Multiple search sources (Google, directories, LinkedIn) with different scraping approaches.
**Trade-offs:** Easy to add sources; each source may need different selectors/timeouts.

**Example:**
```typescript
interface Source {
  name: string;
  search(query: string): Promise<SearchResult[]>;
  scrape(url: string): Promise<RawPage>;
  selectors: Record<string, string>;
}

class GoogleSource implements Source { /* ... */ }
class DirectorySource implements Source { /* ... */ }
```

### Pattern 3: Repository (Data Access Abstraction)

**What:** Abstracts storage operations behind a clean interface.
**When to use:** Managing lead persistence, caching, and deduplication.
**Trade-offs:** Decouples business logic from storage; enables easy switching between JSON/SQLite/DB.

**Example:**
```typescript
interface LeadRepository {
  save(lead: Lead): Promise<void>;
  findByDomain(domain: string): Promise<Lead | null>;
  findAll(): Promise<Lead[]>;
  deduplicate(leads: Lead[]): Lead[];
}
```

## Data Flow

### Request Flow (Single Lead)

```
[CLI Command]
    │
    ▼
[Source Manager] ── discovers URLs via search query
    │
    ▼
[Scraper] ── fetches HTML (HTTP or browser)
    │
    ▼
[Parser] ── extracts name, description, links from HTML
    │
    ▼
[Contact Extractor] ── finds emails, phones, social links
    │
    ▼
[Lead Normalizer] ── standardizes format, validates data
    │
    ▼
[Deduplicator] ── checks against existing leads
    │
    ▼
[Lead Store] ── persists to storage
    │
    ▼
[CSV Export] ── writes to CSV file
```

### State Management

CLI tools are stateless between invocations. State lives in:
- **Config files:** API keys, source preferences (dotenv, JSON)
- **Cache:** Raw scraped responses (JSON files, retry without re-scrape)
- **Lead store:** Accumulated leads (JSON or SQLite)
- **Session state:** Runtime state within a single invocation (in-memory)

### Key Data Flows

1. **Discovery → Extraction:** Source discovers URLs → Scraper fetches → Parser extracts → Contact extractor finds contact info
2. **Enrichment → Storage:** Raw data → Normalized Lead → Deduplication check → Persisted
3. **Export:** All leads → Column mapping → CSV write

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|-------------------------|
| 0-100 leads | Single script (Level 1), in-memory, direct output |
| 100-10K leads | Add caching, lead store, retry logic (Level 2) |
| 10K-100K leads | Queue-based with Redis, distributed scraping, proxy rotation |
| 100K+ leads | Managed platform (Apify, Bright Data) or distributed workers |

### Scaling Priorities

1. **First bottleneck: Rate limiting/blocking** — Add delays, rotate user-agents, use proxies
2. **Second bottleneck: Storage** — Move from JSON to SQLite or PostgreSQL
3. **Third bottleneck: Throughput** — Add concurrent workers, distributed queue

## Anti-Patterns

### Anti-Pattern 1: Monolithic Scraper

**What people do:** Put all scraping, parsing, and extraction logic in one file with conditionals per source.
**Why it's wrong:** Adding a new source requires modifying every conditional; testing is painful; selectors bleed everywhere.
**Do this instead:** Use the Strategy pattern with source adapters. Each source implements a common interface.

### Anti-Pattern 2: No Deduplication

**What people do:** Append every scraped result to CSV without checking for duplicates.
**Why it's wrong:** Same leads from different sources create duplicates; wasted effort; poor user experience.
**Do this instead:** Deduplicate by domain or normalized email before storage.

### Anti-Pattern 3: Inline Secrets

**What people do:** Hardcode API keys or credentials in source files.
**Why it's wrong:** Commits to git; exposed in CI logs; hard to rotate.
**Do this instead:** Use dotenv with .env.example committed to repo; load secrets from environment at runtime.

### Anti-Pattern 4: Blocking on Errors

**What people do:** Throw on any scraping error, aborting the entire batch.
**Why it's wrong:** One bad URL kills the run; no partial results.
**Do this instead:** Log errors, continue processing, collect failed URLs for retry.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Google Search | HTTP scraping with SERP parsing | High blocking risk; consider Google Custom Search API |
| Business Directories | HTTP + selectors | Lower risk; structured listings |
| Websites | Direct HTTP or browser | Variable; handle CAPTCHAs and blocks |
| Proxy Services | Configurable per-request | Bright Data, ScraperAPI, Oxylabs |
| Email Verification | API calls for validation | Never required for MVP |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI ↔ Core | Direct function calls | CLI commands call core orchestrator |
| Core ↔ Extractors | Strategy interface | Inject scraper implementations |
| Extractors ↔ Storage | Repository interface | Abstract persistence |
| Storage ↔ Export | In-memory data | Load leads, pass to CSV generator |

## Build Order Implications

Dependencies决定了哪些组件应该先构建：

```
Phase 1: CLI Foundation
  └─ CLI Parser + Config → enables manual testing

Phase 2: Basic Extraction
  └─ Scraper + Parser + Contact Extractor → core value

Phase 3: Persistence
  └─ Lead Store + Deduplication → accumulates results

Phase 4: Multi-Source
  └─ Source Strategy pattern → scales to multiple sources

Phase 5: Export
  └─ CSV Generator → delivers final output

Phase 6: Resilience
  └─ Rate limiting + Retry + Caching → production reliability
```

**Critical path:** CLI → Extraction → Storage → Export. Multi-source and resilience can be layered on top.

## Sources

- [Crawlee Architecture Overview](https://crawlee.dev/python/docs/guides/architecture-overview) (HIGH confidence)
- [Web Scraping Architecture Patterns: From Prototype to Production](https://use-apify.com/blog/web-scraping-architecture-patterns) (HIGH confidence)
- [Node.js CLI Best Practices](https://github.com/lirantal/nodejs-cli-apps-best-practices) (MEDIUM confidence)
- [Build a CLI with Node.js: Commander vs yargs vs oclif](https://www.pkgpulse.com/blog/how-to-build-cli-nodejs-commander-yargs-oclif) (MEDIUM confidence)

---

*Architecture research for: Lead Generation CLI Tool*
*Researched: 2026-04-03*
