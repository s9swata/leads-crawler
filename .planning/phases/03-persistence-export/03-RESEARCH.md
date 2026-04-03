# Phase 3: Persistence & Export - Research

**Researched:** 2026-04-03
**Domain:** Lead storage, deduplication, filtering, sorting, CSV export
**Confidence:** HIGH

## Summary

Phase 3 implements lead persistence between runs with SQLite storage, automatic deduplication on email/domain, filtering by data completeness, sorting, and CSV export with column selection. The stack uses Python's built-in sqlite3 (or SQLAlchemy Core for better ergonomics) for storage, with stdlib csv module for export. Deduplication uses email normalization and domain extraction; filters use SQL queries; export uses csv.writer with column mapping.

**Primary recommendation:** Use SQLAlchemy Core 2.x with SQLite for lead storage (provides better query builder, type safety, migrations path), stdlib csv for export with column selection, and implement deduplication at insert time using normalized email/domain keys.

---

## User Constraints (from context)

*(No CONTEXT.md exists - using roadmap and Phase 1/2 decisions as constraints)*

### Locked Decisions (from ROADMAP.md & Phase 1/2)
- Stack: Python 3.10+, Click for CLI, Pydantic for config
- Lead schema already defined with source, source_url, discovered_at fields (Phase 1)
- Project uses Poetry for dependency management
- Extraction infrastructure using Crawl4ai already built (Phase 2)
- Deliverables: Lead store (SQLite), deduplication engine, filter engine, sort engine, CSV generator, view command

### Claude's Discretion
- Use raw sqlite3 vs SQLAlchemy for storage
- Use Rich for CLI tables vs plain text
- Deduplication algorithm specifics (exact match vs fuzzy)
- Pagination implementation approach

### Deferred Ideas (OUT OF SCOPE)
- Cloud database (PostgreSQL) - future phase
- Real-time sync between runs
- Advanced CRM integration beyond CSV

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **SQLAlchemy Core** | 2.x | SQLite ORM/query builder | Type-safe, portable, migrations path, active development (v2.0.48 March 2026) |
| **sqlite3** | stdlib | SQLite driver | Built-in, zero config |
| **csv** | stdlib | CSV generation | Built-in, standard format output |
| **pydantic** | 2.x | Lead model validation | Already in stack, integrates with SQLAlchemy |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **rich** | 13.x | CLI table output | When building formatted tables in terminal |
| **tabulate** | 0.9.x | Simple table rendering | For quick table output without Rich overhead |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLAlchemy | raw sqlite3 | More code but zero deps; SQLAlchemy provides query builder, type safety |
| CSV module | pandas | Zero deps vs heavyweight; csv module sufficient for this use case |
| Rich tables | click.echo tables | Rich has better formatting but more deps; use tabulate for simplicity |

---

## Architecture Patterns

### Recommended Project Structure

```
src/
├── cli/                    # CLI entry point (Phase 1)
├── config/                 # Configuration (Phase 1)
├── core/                   # Core types, rate limiter, robots (Phase 1)
├── extraction/            # Core extraction (Phase 2)
├── storage/               # NEW: Lead persistence
│   ├── __init__.py
│   ├── database.py        # SQLAlchemy setup, session
│   ├── lead_repo.py      # Lead repository pattern
│   ├── deduplicator.py   # Deduplication logic
│   └── models.py          # SQLAlchemy Lead model
├── export/                # NEW: Export functionality
│   ├── __init__.py
│   ├── csv_generator.py  # CSV export with column selection
│   └── columns.py         # Column definitions/mapping
└── cli/
    ├── commands.py       # CLI commands (update)
    └── view.py           # Lead viewing with pagination
```

### Pattern 1: SQLAlchemy Core with SQLite

```python
# Source: https://docs.sqlalchemy.org/orm/quickstart.html
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import Session
from datetime import datetime

# Database setup
engine = create_engine("sqlite:///leads.db")
metadata = MetaData()

# Lead table definition
leads = Table('leads', metadata,
    Column('id', String, primary_key=True),
    Column('company_name', String, nullable=False),
    Column('email', String),
    Column('website', String),
    Column('phone', String),
    Column('linkedin', String),
    Column('source', String),
    Column('source_url', String),
    Column('discovered_at', DateTime, default=datetime.utcnow),
    Column('scraped_at', DateTime),
)

metadata.create_all(engine)

# Usage
with Session(engine) as session:
    result = session.execute(
        select(leads).where(leads.c.email.is_not(None))
    )
    leads = result.fetchall()
```

### Pattern 2: Lead Repository Pattern

```python
# Source: Repository pattern - common in Python data apps
from sqlalchemy import select
from datetime import datetime
from typing import Optional

class LeadRepository:
    """Repository for Lead CRUD operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add(self, lead: Lead) -> Lead:
        """Add a lead, return with ID."""
        self.session.execute(
            leads.insert().values(**lead.model_dump())
        )
        self.session.commit()
        return lead
    
    def find_by_email(self, email: str) -> Optional[Lead]:
        """Find lead by email."""
        result = self.session.execute(
            select(leads).where(leads.c.email == email)
        )
        row = result.fetchone()
        return self._row_to_lead(row) if row else None
    
    def find_by_website_domain(self, domain: str) -> list[Lead]:
        """Find leads by website domain."""
        result = self.session.execute(
            select(leads).where(leads.c.website.like(f'%{domain}%'))
        )
        return [self._row_to_lead(row) for row in result.fetchall()]
    
    def list_all(self, limit: int = 100, offset: int = 0) -> list[Lead]:
        """List leads with pagination."""
        result = self.session.execute(
            select(leads).limit(limit).offset(offset)
        )
        return [self._row_to_lead(row) for row in result.fetchall()]
```

### Pattern 3: Deduplication at Insert Time

```python
# Source: Standard deduplication approach for lead data
import re
from urllib.parse import urlparse
from typing import Optional

class Deduplicator:
    """Handles lead deduplication logic."""
    
    def normalize_email(self, email: str) -> Optional[str]:
        """Normalize email for comparison."""
        if not email:
            return None
        return email.lower().strip()
    
    def extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        if not url:
            return None
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return None
    
    def get_dedup_key(self, lead: Lead) -> tuple[str, str]:
        """Generate deduplication key from lead."""
        email_key = self.normalize_email(lead.email) or ""
        domain_key = self.extract_domain(lead.website) or ""
        return (email_key, domain_key)
    
    def is_duplicate(self, lead: Lead, existing: list[Lead]) -> bool:
        """Check if lead is duplicate of any in list."""
        key = self.get_dedup_key(lead)
        for ex in existing:
            ex_key = self.get_dedup_key(ex)
            # Match on email OR domain
            if key[0] and key[0] == ex_key[0]:
                return True
            if key[1] and key[1] == ex_key[1]:
                return True
        return False
```

### Pattern 4: CSV Export with Column Selection

```python
# Source: Python csv module documentation
import csv
from typing import Optional
from enum import Enum

class LeadColumns(Enum):
    """Available columns for export."""
    ID = "id"
    COMPANY = "company_name"
    EMAIL = "email"
    WEBSITE = "website"
    PHONE = "phone"
    LINKEDIN = "linkedin"
    SOURCE = "source"
    SOURCE_URL = "source_url"
    DISCOVERED_AT = "discovered_at"
    SCRAPED_AT = "scraped_at"

COLUMN_MAPPING = {
    "id": "id",
    "company": "company_name",
    "email": "email",
    "website": "website",
    "phone": "phone",
    "linkedin": "linkedin",
    "source": "source",
    "source_url": "source_url",
    "discovered": "discovered_at",
    "scraped": "scraped_at",
}

def export_to_csv(
    leads: list[Lead],
    filepath: str,
    columns: list[str],
    include_header: bool = True
) -> int:
    """Export leads to CSV with selected columns.
    
    Returns number of rows exported.
    """
    # Resolve column names
    fieldnames = []
    for col in columns:
        if col in COLUMN_MAPPING:
            fieldnames.append(COLUMN_MAPPING[col])
        else:
            raise ValueError(f"Unknown column: {col}")
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        
        if include_header:
            writer.writeheader()
        
        for lead in leads:
            row = {field: str(getattr(lead, field, '') or '') 
                   for field in fieldnames}
            writer.writerow(row)
    
    return len(leads)
```

### Pattern 5: Filter and Sort Query Building

```python
# Source: SQLAlchemy filter patterns
from sqlalchemy import select, and_, or_, desc, asc

def build_filter_query(
    session: Session,
    has_email: Optional[bool] = None,
    has_phone: Optional[bool] = None,
    has_website: Optional[bool] = None,
    source: Optional[str] = None,
    sort_by: str = "discovered_at",
    sort_order: str = "desc",
) -> list[Lead]:
    """Build filtered and sorted query."""
    conditions = []
    
    if has_email is not None:
        if has_email:
            conditions.append(leads.c.email.is_not(None))
        else:
            conditions.append(leads.c.email.is_(None))
    
    if has_phone is not None:
        if has_phone:
            conditions.append(leads.c.phone.is_not(None))
        else:
            conditions.append(leads.c.phone.is_(None))
    
    if has_website is not None:
        if has_website:
            conditions.append(leads.c.website.is_not(None))
        else:
            conditions.append(leads.c.website.is_(None))
    
    if source:
        conditions.append(leads.c.source == source)
    
    query = select(leads)
    if conditions:
        query = query.where(and_(*conditions))
    
    # Apply sorting
    sort_column = getattr(leads.c, sort_by, leads.c.discovered_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    result = session.execute(query)
    return [row_to_lead(row) for row in result.fetchall()]
```

### Pattern 6: CLI View with Pagination

```python
# Source: Click documentation with pagination patterns
import click

@click.command('leads')
@click.option('--page', '-p', default=1, help='Page number')
@click.option('--per-page', '-n', default=20, help='Items per page')
@click.option('--filter-email/--no-email', default=None, 
              help='Filter by email presence')
@click.option('--sort', '-s', default='discovered_at',
              type=click.Choice(['discovered_at', 'source', 'company_name']))
def list_leads(page, per_page, filter_email, sort):
    """List leads with pagination."""
    offset = (page - 1) * per_page
    
    # Get leads from repository
    leads = repo.list_all(limit=per_page, offset=offset)
    total = repo.count()
    total_pages = (total + per_page - 1) // per_page
    
    # Display
    click.echo(f"Showing {len(leads)} of {total} leads (page {page}/{total_pages})")
    click.echo("-" * 80)
    
    for lead in leads:
        email = lead.email or "(no email)"
        click.echo(f"{lead.company_name} | {email} | {lead.source}")
    
    if page < total_pages:
        click.echo(f"\nRun with --page {page + 1} for more")
</script>
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| **SQL database** | Raw SQLite with string queries | SQLAlchemy Core | Type safety, query builder, migrations, portable |
| **CSV generation** | String concatenation | csv module | Handles escaping, edge cases, standard format |
| **Email normalization** | Custom lowercase only | Lowercase + strip | Simple is sufficient; complex normalization rarely needed |
| **URL parsing** | Custom regex | urllib.parse | Built-in, handles edge cases |

**Key insight:** For this use case, SQLite + SQLAlchemy Core provides sufficient power without the complexity of full ORM. The csv module is perfect for standard CSV output that works with Excel/Google Sheets.

---

## Common Pitfalls

### Pitfall 1: Duplicate Leads Not Caught at Insert Time
**What goes wrong:** Same lead added multiple times across runs
**Why it happens:** No deduplication check before insert
**How to avoid:** Check for existing email/domain before inserting; use unique constraints where possible
**Warning signs:** Users report seeing same company multiple times

### Pitfall 2: CSV Output Not Opening in Excel
**What goes wrong:** Special characters break Excel import, encoding issues
**Why it happens:** Not specifying encoding, not handling commas in fields
**How to avoid:** Use csv module with utf-8 encoding; quote fields as needed (csv module handles this)
**Warning signs:** Users report garbled characters, broken columns

### Pitfall 3: Filter Queries Not Using Indexes
**What goes wrong:** Slow queries on large lead databases
**Why it happens:** Not creating indexes on frequently filtered columns
**How to avoid:** Create indexes on email, website, source, discovered_at
**Warning signs:** Query time increases linearly with lead count

### Pitfall 4: Deduplication Only on Exact Email Match
**What goes wrong:** Same company with different email formats treated as different
**Why it happens:** Not normalizing email or checking domain
**How to avoid:** Normalize emails (lowercase), check domain match for website
**Warning signs:** Users report "obvious" duplicates not caught

### Pitfall 5: Pagination Not Accounting for Deleted/Filtered Records
**What goes wrong:** Page calculation wrong after leads removed or filtered
**Why to avoid:** Recalculate count on each page request
**Warning signs:** "Page 2" has no results after deleting from page 1

---

## Code Examples

### Complete Storage Module

```python
# src/storage/database.py
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime
from sqlalchemy.orm import Session
from datetime import datetime

engine = create_engine("sqlite:///leads.db", echo=False)
metadata = MetaData()

leads_table = Table('leads', metadata,
    Column('id', String, primary_key=True),
    Column('company_name', String, nullable=False),
    Column('email', String),
    Column('website', String),
    Column('phone', String),
    Column('linkedin', String),
    Column('source', String, default='search'),
    Column('source_url', String),
    Column('discovered_at', DateTime, default=datetime.utcnow),
    Column('scraped_at', DateTime),
)

metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
```

```python
# src/storage/lead_repo.py
from sqlalchemy import select, func
from src.storage.database import leads_table, get_session
from src.core.types import Lead
from typing import Optional

class LeadRepository:
    def add(self, lead: Lead) -> Lead:
        with get_session() as session:
            session.execute(
                leads_table.insert().values(**lead.model_dump())
            )
            session.commit()
        return lead
    
    def count(self) -> int:
        with get_session() as session:
            result = session.execute(select(func.count()).select_from(leads_table))
            return result.scalar() or 0
    
    def list_(self, limit: int = 20, offset: int = 0) -> list[Lead]:
        with get_session() as session:
            result = session.execute(
                select(leads_table).limit(limit).offset(offset)
            )
            return [self._row_to_lead(row) for row in result.fetchall()]
    
    def _row_to_lead(self, row) -> Lead:
        return Lead(**dict(row._mapping))
```

```python
# src/export/csv_generator.py
import csv
from src.core.types import Lead
from typing import Optional

DEFAULT_COLUMNS = [
    'company_name', 'email', 'website', 'phone', 'source', 'discovered_at'
]

def export_csv(
    leads: list[Lead],
    path: str,
    columns: Optional[list[str]] = None
) -> None:
    cols = columns or DEFAULT_COLUMNS
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        writer.writeheader()
        
        for lead in leads:
            row = {col: str(getattr(lead, col, '') or '') for col in cols}
            writer.writerow(row)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| JSON file storage | SQLite | Pre-2020 | Query capability, ACID, better scaling |
| Custom CSV generation | csv module | Pre-2020 | Standard library, handles edge cases |
| Fuzzy deduplication | Exact email + domain match | 2020+ | Simpler, faster, sufficient for most cases |
| Server-side cursor | Client-side pagination | 2020+ | Simpler for CLI, sufficient data size |

**Deprecated/outdated:**
- **shelve module**: Use SQLite instead
- **pandas for CSV**: Use csv module unless pandas already needed
- **fuzzy matching for deduplication**: Overkill; email/domain exact match usually sufficient

---

## Open Questions

1. **Should we use SQLAlchemy or raw sqlite3?**
   - What we know: SQLAlchemy Core provides query builder, type safety, migrations path
   - What's unclear: Additional dependency vs simplicity of raw sqlite3
   - Recommendation: Use SQLAlchemy Core (more maintainable, portable)

2. **Should deduplication be at insert time or batch?**
   - What we know: Insert-time deduplication prevents duplicates from being added
   - What's unclear: Performance with large batch inserts
   - Recommendation: Check before insert for small batches; batch dedup for large imports

3. **What format for discovered_at in CSV?**
   - What we know: ISO format preferred by Excel (YYYY-MM-DD HH:MM:SS)
   - What's unclear: Need timezone handling?
   - Recommendation: Use ISO format with UTC; let user convert if needed

4. **Should we add "completeness score" filter?**
   - What we know: Can calculate based on filled fields
   - What's unclear: Complexity vs utility
   - Recommendation: Start with simple has_email/has_phone filters; add completeness later if needed

---

## Sources

### Primary (HIGH confidence)
- [SQLAlchemy 2.0 Documentation - ORM Quick Start](https://sqlalchemy.org/docs/orm/quickstart.html) - Official docs, v2.0.48, March 2026
- [Python csv module documentation](https://docs.python.org/library/csv.html) - Official stdlib docs
- [urllib.parse documentation](https://docs.python.org/library/urllib.parse.html) - Official stdlib

### Secondary (MEDIUM confidence)
- [WebSearch: Python SQLite best practices 2025](https://climbtheladder.com/10-python-sqlite-best-practices/) - Verified patterns
- [WebSearch: Click CLI pagination patterns](https://click.palletsprojects.com/en/stable/) - Official Click docs

### Tertiary (LOW confidence)
- Phase 1/2 research files - Already established constraints

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - SQLite, SQLAlchemy, csv all well-documented and stable
- Architecture: HIGH - Based on project roadmap and established patterns
- Pitfalls: MEDIUM - Known patterns but implementation specifics depend on testing

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (30 days - stable libraries)