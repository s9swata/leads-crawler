---
phase: 05-resilience-polish
plan: 02
subsystem: resilience
tags: retry, exponential-backoff, dry-run, cli, httpx, crawl4ai

# Dependency graph
requires:
  - phase: 04-search-discovery
    provides: SerperAdapter with search functionality
  - phase: 02-core-extraction
    provides: Crawl4aiAdapter for web scraping
provides:
  - Generic @retry decorator with exponential backoff
  - --dry-run flag for search and scrape commands
affects: [search, scrape, adapters]

# Tech tracking
tech-stack:
  added: [typing-extensions]
  patterns: [retry decorator with ParamSpec for type-safe decorators]

key-files:
  created: [src/core/retry.py]
  modified: [src/search/adapters/serper.py, src/extraction/adapters/crawl4ai_adapter.py, src/cli/commands.py]

key-decisions:
  - "Used typing-extensions ParamSpec for type-safe decorator"

patterns-established:
  - "Generic retry decorator that works with both sync and async functions"
  - "Dry-run mode for previewing CLI operations without side effects"

# Metrics
duration: 2min 16sec
completed: 2026-04-03
---

# Phase 5 Plan 2: Retry Decorator & Dry-Run Summary

**Generic @retry decorator with exponential backoff applied to adapters, --dry-run flag for search/scrape commands**

## Performance

- **Duration:** 2 min 16 sec
- **Started:** 2026-04-03T13:54:23Z
- **Completed:** 2026-04-03T13:56:49Z
- **Tasks:** 4 (5 originally, but Task 3 applied with Task 2)
- **Files modified:** 4

## Accomplishments
- Created generic @retry decorator supporting both sync and async functions
- Applied retry to SerperAdapter with exponential backoff (5 retries, 1s initial, 2x factor)
- Applied retry to Crawl4aiAdapter with exponential backoff (3 retries, 2s initial, 2x factor)
- Added --dry-run flag to search command for previewing queries
- Added --dry-run flag to scrape command for previewing URL scraping

## Task Commits

Each task was committed atomically:

1. **Task 1: Create generic retry decorator** - `bb135cd` (feat)
2. **Task 2: Apply retry to SerperAdapter** - `eb3780e` (feat)
3. **Task 3: Apply retry to Crawl4aiAdapter** - `eb3780e` (feat, combined with Task 2)
4. **Task 4: Add --dry-run to search command** - `735a327` (feat)
5. **Task 5: Add --dry-run to scrape command** - `735a327` (feat, combined with Task 4)

**Plan metadata:** (to be committed)

## Files Created/Modified
- `src/core/retry.py` - Generic retry decorator with exponential backoff, jitter
- `src/search/adapters/serper.py` - Updated to use @retry decorator
- `src/extraction/adapters/crawl4ai_adapter.py` - Updated to use @retry decorator
- `src/cli/commands.py` - Added --dry-run flag to search and scrape commands

## Decisions Made
- Used typing-extensions ParamSpec for type-safe decorator that preserves function signatures
- Replaced custom retry logic in SerperAdapter with standardized @retry decorator
- Dry-run mode skips API key check to allow preview without credentials

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Task 3 (Crawl4aiAdapter) - The fetch_if_allowed method is in base class, so applied @retry to the underlying fetch method instead

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Retry infrastructure in place for all adapters
- Dry-run mode available for safe CLI operation preview
- Ready for further resilience improvements or feature work

---
*Phase: 05-resilience-polish*
*Completed: 2026-04-03*
