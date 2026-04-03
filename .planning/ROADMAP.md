# Roadmap: Lead Generation Tool

**Version:** 1.0
**Created:** 2026-04-03
**Based on:** REQUIREMENTS.md (17 v1 requirements)

## Overview

5 phases delivering a production-ready CLI tool for aggregating contact data from free sources and exporting to CSV.

---

## Phase 1: Foundation

**Goal:** Establish CLI scaffold, configuration management, rate limiting framework, and lead data schema.

### Success Criteria

1. User runs `lead-gen --help` and sees documented command structure
2. User passes `--config` with API keys and tool loads config without errors
3. Tool respects robots.txt directives and logs compliance decisions
4. Tool enforces rate limits and logs throttling decisions
5. Tool validates lead data against schema and rejects invalid entries

### Requirements Addressed

| ID | Requirement | Verification |
|----|-------------|--------------|
| CLI-01 | Tool provides CLI with help documentation | `--help` output is comprehensive |
| CLI-02 | Tool supports configuration via flags | `--config`, `--rate-limit` flags work |
| CLI-03 | Tool displays progress during operations | Progress logs visible in output |
| DISC-04 | Tool aggregates from free sources | Rate limiting framework in place |

### Deliverables

- CLI entry point with Click framework
- Config loader (.env, YAML, JSON support)
- Rate limiter with crawl-delay respect
- robots.txt parser
- Lead schema with validation

**Plans:**
- [ ] 01-01-PLAN.md — CLI scaffold and configuration management
- [ ] 01-02-PLAN.md — Rate limiting, robots.txt parsing, lead schema

---

## Phase 2: Core Extraction

**Goal:** Build web scraping and contact data extraction capabilities.

### Success Criteria

1. User provides a URL and tool extracts emails within 10 seconds
2. User provides a URL and tool extracts phone numbers when present
3. User provides a URL and tool extracts social links (LinkedIn, Twitter/X)
4. User provides a URL and tool extracts website URLs from page
5. Extraction handles JavaScript-rendered pages without errors

### Requirements Addressed

| ID | Requirement | Verification |
|----|-------------|--------------|
| COLL-01 | Tool extracts email addresses | Test with known email page |
| COLL-02 | Tool extracts phone numbers | Test with known phone page |
| COLL-03 | Tool extracts social media links | Test with known social page |
| COLL-04 | Tool extracts website URLs | Test with known link page |

### Deliverables

- HTTP/browser scraper (Crawl4ai)
- HTML parser with BeautifulSoup
- Email extractor (regex + pattern matching)
- Phone number extractor
- Social link extractor (LinkedIn, Twitter/X)
- Source adapter interface (Strategy pattern)

**Plans:**
- [ ] 02-01-PLAN.md — Extraction infrastructure (scraper + extractors)
- [ ] 02-02-PLAN.md — Source adapter interface and CLI integration

---

## Phase 3: Persistence & Export

**Goal:** Store leads between runs, deduplicate, and enable CSV export with column selection.

### Success Criteria

1. User runs search twice with same query and sees no duplicate leads
2. User filters leads by "has email" and sees only leads with emails
3. User sorts leads by source timestamp and sees chronological order
4. User exports to CSV and file opens correctly in Excel/Google Sheets
5. User selects specific columns and exported CSV contains only selected

### Requirements Addressed

| ID | Requirement | Verification |
|----|-------------|--------------|
| LEAD-01 | User can view leads in list format | CLI displays formatted lead table |
| LEAD-02 | Tool removes duplicate leads | Deduplication test passes |
| LEAD-03 | User can filter by data completeness | Filter flags work correctly |
| LEAD-04 | User can sort by source/timestamp | Sort flags work correctly |
| EXPT-01 | User can export leads to CSV | CSV file is created |
| EXPT-02 | User can select columns | Column flags filter output |
| EXPT-03 | CSV is standard format | Opens in Excel/CRM tools |

### Deliverables

- Lead store (SQLite or JSON)
- Deduplication engine (email + domain)
- Filter engine (completeness, source, timestamp)
- Sort engine
- CSV generator with column mapping
- View command with pagination

---

## Phase 4: Search & Discovery

**Goal:** Integrate search sources (Google, directories) to discover leads from search queries.

### Success Criteria

1. User runs `lead-gen search "web development agency" --location Austin` and sees results
2. User runs search and sees progress updates during scraping
3. Tool discovers leads from multiple search result pages
4. Tool handles rate limits gracefully without crashing
5. User sees source attribution for each lead

### Requirements Addressed

| ID | Requirement | Verification |
|----|-------------|--------------|
| DISC-01 | User can search by keyword | Search returns keyword-matched leads |
| DISC-02 | User can search by location | Search returns location-matched leads |
| DISC-03 | User can combine keyword and location | Combined search works |

### Deliverables

- Serper.dev integration (Google Search API)
- Search query builder
- Search result parser
- Multi-page result handling
- Source attribution in lead data

---

## Phase 5: Resilience & Polish

**Goal:** Production hardening—retry logic, error recovery, progress reporting, and user experience improvements.

### Success Criteria

1. User runs long scrape that fails mid-way; tool resumes from checkpoint
2. User sees clear error messages for common failure modes
3. User runs dry-run mode and sees what would happen without executing
4. User experiences no data loss on network failures (retry succeeds)
5. User completes full workflow (search → view → filter → export) without errors

### Deliverables

- Checkpoint/resume system
- Retry with exponential backoff
- Dry-run mode
- Error handling with user-friendly messages
- Progress bars and status indicators
- Graceful shutdown handling

---

## Phase Order Rationale

1. **Foundation first** — Legal compliance and rate limiting are architectural foundations that cannot be retrofitted
2. **Core extraction second** — Scraping is the primary value; build on foundation, not before it
3. **Persistence before search** — Storage abstraction enables clean source additions later
4. **Search integration third** — Connect discovered URLs to extraction pipeline
5. **Resilience last** — Progressive enhancement after core loop works; don't add complexity before validating the basic flow

---

## Dependencies

```
Phase 1 ─┬─► Phase 2 ─┬─► Phase 3 ─┬─► Phase 4 ─┬─► Phase 5
         │            │            │            │
         └────────────┴────────────┴────────────┘
              (all phases use foundation)
```

---

*Roadmap created: 2026-04-03*
