# Lead Generation Tool

## What This Is

A lead generation CLI tool for web development agencies that aggregates contact data from free sources (Google Search, LinkedIn, public directories) and exports leads to CSV for cold outreach campaigns.

## Core Value

Deliver actionable leads with verified contact info in a downloadable CSV that sales teams can immediately use for cold calling and email campaigns.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can search for leads by keyword/industry/location
- [ ] Tool aggregates emails, phone numbers, social links, and websites from search results
- [ ] User can export leads to CSV file
- [ ] User can filter/sort leads before export
- [ ] User can save and reload search configurations

### Out of Scope

- Email verification/sending — just collection, not outreach
- CRM integration — CSV export only
- Paid data sources — free sources only
- Real-time monitoring/alerting

## Context

Built for a web development agency that needs to find potential clients. Current process is manual Google searches and manual data entry — time-consuming and inconsistent.

## Constraints

- **Tech**: Must use only free/no-cost APIs and scraping methods
- **Legal**: Must respect robots.txt and rate limits; no bypassing paywalls
- **Output**: Must produce standard CSV format compatible with common CRM tools

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI-first approach | Developers/agencies prefer command-line efficiency | — Pending |
| CSV-only export | Most universal format for cold outreach tools | — Pending |

---
*Last updated: 2026-04-03 after initialization*
