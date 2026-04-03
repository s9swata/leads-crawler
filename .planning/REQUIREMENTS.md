# Requirements: Lead Generation Tool

**Defined:** 2026-04-03
**Core Value:** Deliver actionable leads with verified contact info in a downloadable CSV that sales teams can immediately use for cold calling and email campaigns.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Search & Discovery

- [ ] **DISC-01**: User can search for leads by keyword (e.g., "web development agency", "ecommerce development")
- [ ] **DISC-02**: User can search for leads by location (e.g., "Austin TX", "United Kingdom")
- [ ] **DISC-03**: User can combine keyword and location for targeted searches
- [ ] **DISC-04**: Tool aggregates results from free sources (Google Search, public directories)

### Data Collection

- [ ] **COLL-01**: Tool extracts email addresses from search results and websites
- [ ] **COLL-02**: Tool extracts phone numbers from websites and search results
- [ ] **COLL-03**: Tool extracts social media links (LinkedIn, Twitter/X) from websites
- [ ] **COLL-04**: Tool extracts website URLs from search results

### Lead Management

- [ ] **LEAD-01**: User can view collected leads in a list format
- [ ] **LEAD-02**: Tool automatically removes duplicate leads based on email/website
- [ ] **LEAD-03**: User can filter leads by data completeness (has email, has phone, etc.)
- [ ] **LEAD-04**: User can sort leads by source or extraction timestamp

### Export

- [ ] **EXPT-01**: User can export leads to CSV file
- [ ] **EXPT-02**: User can select which columns to include in export (email, phone, social links, website)
- [ ] **EXPT-03**: Exported CSV is standard format compatible with CRM tools

### CLI Interface

- [ ] **CLI-01**: Tool provides command-line interface with help documentation
- [ ] **CLI-02**: Tool supports configuration via command-line flags
- [ ] **CLI-03**: Tool displays progress during search and scraping operations

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Search & Discovery

- **DISC-05**: User can save and reload search configurations
- **DISC-06**: Tool supports scraping from additional directories (Yellow Pages, niche industry sites)

### Data Collection

- **COLL-05**: Tool verifies email deliverability before export
- **COLL-06**: Tool extracts company size or industry information

### Lead Management

- **LEAD-05**: User can tag/label leads for categorization
- **LEAD-06**: Tool supports multiple workspaces for different clients

### Advanced Features

- **ADVN-01**: Tool scores leads by quality/fit (ICP scoring)
- **ADVN-02**: Tool detects website technology stack (WordPress, Shopify, etc.)
- **ADVN-03**: Tool provides batch processing with resume capability

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Email sending/automation | Dedicated tools (Instantly, lemlist) do this better; deliverability requires specialized infrastructure |
| Built-in CRM integration | CRM APIs are complex; export to CSV is universal approach |
| LinkedIn scraping | Terms of service violations, IP blocking; use Google Maps + websites instead |
| GUI/dashboard | CLI is more efficient for power users; web apps require hosting and auth |
| Real-time email verification on every search | Slows scraping dramatically; batch verify before export instead |
| Paid data sources | Idea specifies free sources only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DISC-01 | TBD | Pending |
| DISC-02 | TBD | Pending |
| DISC-03 | TBD | Pending |
| DISC-04 | TBD | Pending |
| COLL-01 | TBD | Pending |
| COLL-02 | TBD | Pending |
| COLL-03 | TBD | Pending |
| COLL-04 | TBD | Pending |
| LEAD-01 | TBD | Pending |
| LEAD-02 | TBD | Pending |
| LEAD-03 | TBD | Pending |
| LEAD-04 | TBD | Pending |
| EXPT-01 | TBD | Pending |
| EXPT-02 | TBD | Pending |
| EXPT-03 | TBD | Pending |
| CLI-01 | TBD | Pending |
| CLI-02 | TBD | Pending |
| CLI-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 0
- Unmapped: 17 ⚠️

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-03 after initial definition*
