# Phase 5: Resilience & Polish - Research

**Researched:** 2026-04-03  
**Domain:** CLI production hardening, retry logic, checkpoint/resume  
**Confidence:** HIGH

## Summary

This phase adds production-ready resilience features to the CLI tool. The existing codebase already has:
- Exponential backoff in SerperAdapter (lines 56-78)
- tqdm for progress bars
- Session scope context manager for database
- LeadIngestionService with deduplication

This phase builds on those foundations to add checkpoint/resume, comprehensive error handling, dry-run mode, and graceful shutdown.

---

## User Constraints

- Python 3.10+, Click CLI, Pydantic, Crawl4ai, SQLAlchemy, Poetry
- Already has: tqdm, exponential backoff (SerperAdapter), RateLimiter
- SQLite database at `leads.db`
- Uses Strategy pattern for adapters

---

## Checkpoint/Resume System

### Design Options

**Option 1: Database-backed checkpoint table (Recommended)**

```python
# src/storage/models.py - add Checkpoint model
class Checkpoint(Base):
    __tablename__ = "checkpoints"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String, unique=True)  # e.g., "search:query:limit"
    query = Column(String)
    location = Column(String)
    limit = Column(Integer)
    offset = Column(Integer)
    status = Column(String)  # "in_progress", "completed", "failed"
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    error_message = Column(String, nullable=True)
```

**Checkpoint workflow:**
1. Before starting a job, check for existing checkpoint with same job_id
2. If exists and "in_progress", resume from offset
3. If exists and "completed", skip or re-run with --force
4. During execution, periodically update offset
5. On completion, mark as "completed"

**Storage location:** SQLite in same database (leads.db)

### Implementation Pattern

```python
class CheckpointManager:
    def __init__(self, job_id: str):
        self.job_id = job_id
    
    def get_or_create(self) -> Checkpoint:
        # Query existing or create new
        pass
    
    def update_progress(self, offset: int):
        # Update current progress
        pass
    
    def mark_complete(self):
        # Mark job as done
        pass
    
    def mark_failed(self, error: str):
        # Store error for debugging
        pass
```

---

## Retry with Exponential Backoff

### Existing Implementation

The SerperAdapter already has exponential backoff (lines 56-78 in serper.py):

```python
async def _request_with_retry(self, client, headers, data):
    backoff = self.INITIAL_BACKOFF  # 1.0 seconds
    for attempt in range(self.MAX_RETRIES):  # 5 retries
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            await asyncio.sleep(backoff)
            backoff *= 2  # Exponential backoff
```

### Extensions Needed

1. **Crawl4aiAdapter** - Add retry logic for scraping failures
2. **Database operations** - Handle transient DB failures
3. **General utility** - Create reusable retry decorator

**Generic retry decorator:**

```python
import asyncio
from functools import wraps
from typing import TypeVar, Callable

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 60.0,
    backoff_factor: float = 2.0
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            backoff = initial_backoff
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * backoff_factor, max_backoff)
            return None
        return wrapper
    return decorator
```

---

## Dry-Run Mode

### Implementation Approach

Add `--dry-run` flag to commands that make changes:

```python
@click.command(name="search")
@click.option("--dry-run", is_flag=True, help="Show what would happen without executing")
def search(query, location, limit, dry_run):
    if dry_run:
        click.echo(f"Would search for: {query} {location or ''}")
        click.echo(f"Would return up to {limit} results")
        click.echo(f"Would ingest results: {ingest}")
        return
```

### Commands to Add Dry-Run

1. **search** - Show query, location, limit, ingest flag
2. **scrape** - Show URL, extraction targets
3. **export** - Show filter criteria, output path
4. **leads** - Show filter criteria

**Example output:**
```
$ lead-gen search --query "restaurants" --dry-run
Would execute:
  Query: restaurants
  Location: (none)
  Limit: 10
  Ingest: No
```

---

## Error Handling with User-Friendly Messages

### Error Categories to Handle

1. **Configuration errors**
   - Missing API keys
   - Missing database
   - Invalid settings

2. **Network errors**
   - Connection timeout
   - Rate limiting (429)
   - DNS failures
   - SSL errors

3. **Data errors**
   - Invalid URLs
   - Malformed responses
   - Parsing failures

4. **Database errors**
   - Locked database
   - Schema issues
   - Disk full

### Click Exception Handling Pattern

Existing pattern in commands.py (lines 39-42):

```python
if not settings.serper_api_key:
    raise click.ClickException(
        "SERPER_API_KEY not set. Get one at https://serper.dev/ and set it in your .env file."
    )
```

**Extend to cover:**

```python
def handle_network_error(e: Exception) -> None:
    if "timeout" in str(e).lower():
        raise click.ClickException(
            "Request timed out. Check your internet connection and try again."
        )
    elif "429" in str(e):
        raise click.ClickException(
            "Rate limited. Wait a moment before retrying."
        )
    else:
        raise click.ClickException(f"Network error: {e}")
```

---

## Progress Bars and Status Indicators

### Existing Usage

tqdm already in use in commands.py (lines 61-63):

```python
with tqdm(total=limit, desc="Searching", unit="results", leave=True) as pbar:
    results = await adapter.search(full_query, limit)
    pbar.update(len(results))
```

### Extensions Needed

1. **Scrape progress** - Show URL being processed, extraction status
2. **Batch operations** - Progress for export, leads view
3. **Status messages** - "Processing 3/10...", "Extracting emails..."

**Recommended pattern:**

```python
# For multi-step operations
with tqdm(total=len(urls), desc="Scraping", unit="url") as pbar:
    for url in urls:
        try:
            result = await scrape(url)
            pbar.set_postfix({"status": "ok"})
        except Exception as e:
            pbar.set_postfix({"status": "failed"})
        pbar.update(1)
```

---

## Graceful Shutdown Handling

### SIGINT/SIGTERM Handling

```python
import signal
import sys

class GracefulShutdown:
    def __init__(self):
        self.shutdown_requested = False
    
    def request_shutdown(self, signum, frame):
        self.shutdown_requested = True
        click.echo("\nShutdown requested. Saving progress...")
        # Save checkpoint here
    
    def setup(self):
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)
```

### Integration with Checkpoint System

```python
shutdown = GracefulShutdown()
shutdown.setup()

try:
    for batch in batches:
        if shutdown.shutdown_requested:
            checkpoint_manager.update_progress(current_offset)
            click.echo(f"Progress saved at offset {current_offset}")
            break
        await process_batch(batch)
finally:
    # Always save checkpoint on exit
    checkpoint_manager.update_progress(current_offset)
```

---

## Database Schema Additions

### Checkpoint Table

```sql
CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    command TEXT NOT NULL,
    query TEXT,
    location TEXT,
    limit INTEGER,
    offset INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);
```

### Job History Table (Optional)

```sql
CREATE TABLE job_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    command TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    leads_found INTEGER DEFAULT 0,
    leads_ingested INTEGER DEFAULT 0,
    error_message TEXT
);
```

---

## Implementation Plan

### Phase 5.01: Checkpoint System
1. Add Checkpoint model to `src/storage/models.py`
2. Create CheckpointManager in `src/storage/checkpoint.py`
3. Integrate with search command for resume capability

### Phase 5.02: Retry Logic
1. Create retry decorator in `src/core/retry.py`
2. Apply to Crawl4aiAdapter.fetch_if_allowed()
3. Add retry to database operations

### Phase 5.03: Dry-Run Mode
1. Add `--dry-run` flag to search, scrape, export, leads commands
2. Implement preview logic for each command

### Phase 5.04: Error Handling
1. Create error handler module `src/cli/errors.py`
2. Add user-friendly messages for common failures
3. Integrate with all commands

### Phase 5.05: Progress & Shutdown
1. Enhance tqdm usage in batch operations
2. Add graceful shutdown with checkpoint save
3. Add status indicators (spinner, warnings)

---

## Key Files to Modify

1. `src/storage/models.py` - Add Checkpoint model
2. `src/storage/checkpoint.py` - New checkpoint manager
3. `src/core/retry.py` - New retry decorator
4. `src/cli/errors.py` - New error handlers
5. `src/cli/commands.py` - Add flags and integrate features

---

## Dependencies

No new dependencies required:
- **tqdm** - Already in use
- **signal** - Built-in Python
- **sqlite** - Built-in (already using SQLAlchemy)

---

## Sources

- [Click exception handling](https://click.palletsprojects.com/en/8.1.x/exceptions/)
- [tqdm documentation](https://tqdm.github.io/)
- [Python signal handling](https://docs.python.org/3/library/signal.html)
- [Exponential backoff patterns](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

---

## Metadata

**Confidence breakdown:**
- Checkpoint design: HIGH - Simple table-based approach
- Retry logic: HIGH - Already partially implemented
- Dry-run: HIGH - Simple flag-based preview
- Error handling: HIGH - Pattern already exists
- Progress bars: HIGH - tqdm already in use

**Research date:** 2026-04-03  
**Valid until:** 2026-05-03