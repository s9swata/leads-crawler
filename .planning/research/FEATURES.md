# Feature Research

**Domain:** B2B Lead Generation CLI Tool for Web Development Agencies
**Researched:** 2026-04-03
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| CSV Import/Export | Users already have spreadsheets of leads; basic I/O is fundamental | LOW | Standard CSV parsing with header detection |
| Website/URL Scraping | Core value prop; users need business contact info from sites | MEDIUM | HTML parsing, contact extraction, rate limiting |
| Email Collection | Cold outreach requires email addresses; this is the primary deliverable | MEDIUM | Pattern matching, validation, multiple discovery methods |
| Phone Number Extraction | Secondary contact method; agencies want multiple outreach options | MEDIUM | Various formats, international support |
| Social Media Link Extraction | LinkedIn, Twitter/X profiles add credibility and alternative outreach paths | LOW | Follow standard URL patterns, verify profiles exist |
| Lead Deduplication | Users import from multiple sources; duplicates waste outreach effort | LOW | Hash-based comparison, fuzzy matching for slight variations |
| Data Export to CSV | Final output for email tools (Instacart, lemlist, etc.) | LOW | Standard CSV with configurable columns |
| Search/Filter Leads | Users need to narrow down by industry, location, size | MEDIUM | Local filtering, no server required |
| Configurable Output Columns | Different outreach tools need different fields | LOW | User selects which columns to include |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Free Data Sources Only | Avoid per-credit costs that tank margins on high-volume agency work | HIGH | Scrape Google Maps, LinkedIn (public), Yellow Pages, niche directories |
| Local-First Storage | Work offline, version control with git, no vendor lock-in | MEDIUM | SQLite local DB, query without network |
| Agency Multi-Client Support | agencies manage dozens of clients; isolate each client's leads | MEDIUM | Workspace/project separation per client |
| ICP Scoring | Help users find "good" leads (budget, timeline, fit) beyond just contact info | HIGH | Rule-based or ML scoring; requires data enrichment |
| Tech Stack Detection | Agencies can target by website tech (WordPress, Shopify, Webflow) | MEDIUM | BuiltWith-style detection from website HTML |
| Job Title/Role Extraction | Target decision-makers (CEO, Marketing Director) not generic contacts | MEDIUM | LinkedIn parsing, company page analysis |
| AI-Powered Enrichment Chat | Natural language queries: "find e-commerce sites with >50 employees" | HIGH | Local LLM or API integration |
| Company Size Detection | Filter by small/medium/enterprise for pricing tier targeting | LOW | Employee count from LinkedIn, Crunchbase, website signals |
| Funding Stage Detection | Target recently funded companies (Series A, B) with upgrade needs | MEDIUM | Crunchbase, PitchBook, news scraping |
| Website Quality Scoring | Filter by website sophistication (custom code vs WordPress templates) | MEDIUM | Technical depth analysis |
| CLI Native UX | Power users expect proper CLI: flags, pipes, jq compatibility | MEDIUM | Proper argument parsing, stdin/stdout |
| Batch/Parallel Processing | Process thousands of leads without babysitting | MEDIUM | Concurrency, progress reporting, resume on failure |
| MCP Server Integration | AI assistants (Cursor, Claude) can invoke lead generation mid-conversation | MEDIUM | Anthropic MCP protocol, stateless tool calls |
| Scriptability | Cron jobs, webhooks, CI pipelines for automated workflows | MEDIUM | Environment variables, exit codes, idempotent operations |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Built-in Email Sending | Seems convenient to have everything in one tool | Deliverability requires dedicated infrastructure; spam rules change constantly; becomes a different product (outbound automation) | Export to CSV → use Instantly.ai or lemlist for sending |
| Real-time Email Verification on Every Search | Users want guaranteed deliverable emails | Slows down scraping dramatically; verification APIs cost money; false confidence (server changes happen) | Batch verify before export, not during discovery |
| GUI/Dashboard | "Non-technical users need it" | Adds massive complexity; web apps need hosting, auth, state management; CLI already has UX patterns for non-tech users (prompts, help text) | Well-designed CLI prompts and documentation |
| LinkedIn Scraping | LinkedIn has the most complete B2B data | Terms of service violations; IP blocking; unreliable; requires accounts; constant cat-and-mouse with LinkedIn's anti-bot | Use Google Maps + company websites + public profiles instead |
| Native CRM Integration | "Sync directly to Salesforce/HubSpot" | CRM APIs are complex; auth/refresh tokens; different field mappings per client; causes support burden | Export CSV → import to CRM |
| Social Media Scraping (Twitter, Instagram) | Social presence seems valuable | Platform ToS restrictions; unreliable; not B2B relevant for agencies | Focus on LinkedIn/public company data |
| White-Labeling | Agencies want to rebrand the tool | Maintenance nightmare; version drift; security surface area | Offer referral program or discount codes instead |
| Multi-Tenant Cloud Architecture | "Store data in the cloud for team access" | GDPR/compliance; hosting costs; authentication; becomes SaaS product, not CLI | Local storage + git sync for teams |
| Mobile App | "Check leads on the go" | Completely different platform; not a CLI use case | Responsive web export viewing or simple status commands |

## Feature Dependencies

```
[CSV Import]
    └──requires──> [Data Cleaning/Dedup]

[Web Scraping]
    └──requires──> [Rate Limiting]
    └──requires──> [Retry Logic]
    └──enhances──> [Email Discovery]

[Email Discovery]
    └──requires──> [Email Validation]

[Social Link Extraction]
    └──requires──> [URL Validation]

[Multi-Client Workspaces]
    └──requires──> [Local Database]

[ICP Scoring]
    └──requires──> [Data Enrichment]
    └──requires──> [Company Size Detection]

[AI Chat Interface]
    └──requires──> [Local Database]
    └──requires──> [Data Schema Understanding]

[MCP Server]
    └──requires──> [CLI Core]
    └──enhances──> [Scriptability]

[Batch Processing]
    └──requires──> [Resume/Checkpoint]
    └──requires──> [Progress Reporting]
```

### Dependency Notes

- **CSV Import requires Data Cleaning:** Raw imports always have duplicates, missing fields, inconsistent formatting
- **Web Scraping requires Rate Limiting:** Without it, IPs get blocked and the tool becomes unusable
- **Email Discovery enhances with Web Scraping:** Company websites often have contact forms or mailto: links
- **Multi-Client Workspaces requires Local Database:** Each client needs isolated data storage
- **ICP Scoring requires Company Size Detection:** Can't score without firmographic data
- **MCP Server enhances Scriptability:** AI assistants become the orchestration layer
- **Batch Processing requires Resume/Checkpoint:** Agencies can't babysit 10-hour scrapes

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] **CSV Import** — Load existing lead lists; prove the tool handles real-world messy data
- [ ] **Web Scraping** — Extract business info from URLs/domains; the core differentiator
- [ ] **Email Collection** — Find business emails from websites; primary value deliverable
- [ ] **CSV Export** — Close the loop; leads must flow into outreach tools
- [ ] **Lead Deduplication** — Prevent waste; basic hash-based comparison

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] **Social Link Extraction** — Trigger: users ask for LinkedIn/Twitter; adds credibility signals
- [ ] **Phone Number Extraction** — Trigger: multi-channel outreach becomes priority
- [ ] **Multi-Client Workspaces** — Trigger: agency beta users managing 3+ clients
- [ ] **Batch Processing with Progress** — Trigger: users scraping 1000+ leads
- [ ] **Basic Filtering** — Trigger: users need to narrow down by location/industry

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **AI-Powered Enrichment Chat** — Why defer: requires LLM integration, prompt engineering, local model support
- [ ] **ICP Scoring** — Why defer: needs training data, scoring model; not MVP validation
- [ ] **MCP Server** — Why defer: niche use case for AI-forward users; post-MVP
- [ ] **Tech Stack Detection** — Why defer: useful but complex; BuiltWith-style analysis
- [ ] **Funding Stage Detection** — Why defer: requires Crunchbase integration; nice-to-have signal

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| CSV Import/Export | HIGH | LOW | P1 |
| Website Scraping | HIGH | MEDIUM | P1 |
| Email Collection | HIGH | MEDIUM | P1 |
| Lead Deduplication | HIGH | LOW | P1 |
| Phone Extraction | MEDIUM | MEDIUM | P2 |
| Social Link Extraction | MEDIUM | LOW | P2 |
| Multi-Client Workspaces | MEDIUM | MEDIUM | P2 |
| Batch Processing | MEDIUM | MEDIUM | P2 |
| Basic Filtering | MEDIUM | LOW | P2 |
| ICP Scoring | HIGH | HIGH | P3 |
| AI Chat Interface | HIGH | HIGH | P3 |
| Tech Stack Detection | MEDIUM | MEDIUM | P3 |
| MCP Server | MEDIUM | MEDIUM | P3 |
| Funding Stage Detection | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | LeadMagic CLI | Apify (Lead Enrichment) | Lessie AI | Our Approach |
|---------|--------------|-------------------------|-----------|--------------|
| CLI Interface | Yes | Yes (Apify CLI) | No (Web only) | Yes - Core differentiator |
| Free Data Sources | No (API-based enrichment) | No (API credits) | No (credits) | Yes - Scrape free sources |
| Local Storage | Yes (SQLite) | No (cloud only) | No | Yes - Agency preference |
| CSV Import/Export | Yes | Limited | Yes | Yes - Core workflow |
| Web Scraping | Via API | Via actors | Via search | Yes - Primary method |
| Email Discovery | Yes (API) | Yes (API) | Yes | Yes - Multiple methods |
| Agency Multi-Client | Limited | No | No | Yes - First-class support |
| MCP Server | Yes | Yes (Apify MCP) | No | Future consideration |
| Pricing Model | Per-credit | Per-result | Per-search | Free (scraping) + optional paid enrichment |

## Sources

- [LeadMagic CLI](https://leadmagic.io/solutions/cli) - B2B enrichment CLI reference
- [LeadMagic CLI Introduction](https://leadmagic.io/blog/introducing-leadmagic-cli) - CLI workflow patterns
- [Apify Lead Enrichment](https://apify.com/ozapp/lead-enrichment) - Web scraping + enrichment
- [Lessie AI](https://lessie.ai/blog/best-b2b-lead-generation-tools) - AI-powered lead discovery
- [Best Lead Generation Tools 2026](https://www.comparegen.ai/blog/best-ai-lead-generation-tools-2026) - Market overview
- [Email Verification Benchmarks](https://instantly.ai/blog/2026-email-verification-benchmark-accuracy-scores-for-8-top-tools/) - Data quality importance

---
*Feature research for: B2B Lead Generation CLI Tool*
*Researched: 2026-04-03*
