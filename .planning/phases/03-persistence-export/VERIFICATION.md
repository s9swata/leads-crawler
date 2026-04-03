# Phase 03-persistence-export Verification

## Phase Goal
Store leads between runs, deduplicate, and enable CSV export with column selection.

## Must Have Verification Results

### ✅ PASSED

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 2 | User filters leads by "has email" | **IMPLEMENTED** | `src/cli/commands.py:112-114` `--filter-email/--no-email` option; `src/storage/query_builder.py:40-44` implements filter |
| 3 | User sorts leads by source timestamp | **IMPLEMENTED** | `src/cli/commands.py:123-127` `--sort discovered_at` option; `src/storage/query_builder.py:65-69` implements sorting |
| 4 | User exports to CSV, file opens in Excel/Google Sheets | **IMPLEMENTED** | `src/cli/commands.py:175-212` export command; `src/export/csv_generator.py:43` uses UTF-8 encoding |
| 5 | User selects specific columns | **IMPLEMENTED** | `src/cli/commands.py:177` `--columns` option; `src/export/csv_generator.py:35-41` handles column selection |

### ❌ FAILED

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | User runs search twice, sees no duplicates | **NOT IMPLEMENTED** | Deduplicator exists in `src/storage/deduplicator.py` but is never called. No workflow connects search/scrape results to LeadRepository.add(). |

## Analysis

**What was built:**
- `src/storage/database.py` - SQLAlchemy setup with SQLite
- `src/storage/models.py` - Lead model with indexes
- `src/storage/lead_repo.py` - CRUD operations
- `src/storage/deduplicator.py` - Email/domain deduplication logic (defined but unused)
- `src/storage/query_builder.py` - Filter/sort engine
- `src/export/csv_generator.py` - CSV export with column selection
- `src/export/columns.py` - Column definitions
- `src/cli/commands.py` - `leads` and `export` commands

**What's missing:**
- **Lead persistence workflow**: The `search` and `scrape` commands don't store results to the database. The deduplication logic in `Deduplicator` is never invoked because there's no code path that:
  1. Takes search/scrape results
  2. Checks for duplicates using `Deduplicator.find_duplicate()`
  3. Saves to database via `LeadRepository.add()`

**Blocking issue**: Without a workflow that stores leads, requirements 2-5 are functional but only work with manually populated data.

## Recommendation

To complete the phase goal, a lead ingestion workflow is needed that:
1. Accepts leads from search/scrape operations
2. Uses `Deduplicator.find_duplicate()` to check for existing leads
3. Stores unique leads via `LeadRepository.add()`

Without this, the CSV export only works on pre-populated data, not on leads generated from search/scrape runs.