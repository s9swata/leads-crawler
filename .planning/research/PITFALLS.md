# Pitfalls Research

**Domain:** B2B Lead Generation CLI Tool for Web Development Agencies
**Researched:** 2026-04-03
**Confidence:** MEDIUM-HIGH

## Critical Pitfalls

### Pitfall 1: Legal Non-Compliance (robots.txt, ToS, GDPR)

**What goes wrong:**
Tool collects data from sites that explicitly prohibit scraping, leading to IP bans, cease-and-desist letters, or GDPR fines (up to €20M or 4% of global revenue). A single violation can destroy user trust and create personal liability for executives.

**Why it happens:**
Developers focus on technical functionality ("can we collect this?") rather than legal boundaries ("should we?"). The assumption that "public data is free to take" is legally false under GDPR.

**How to avoid:**
- Parse and respect robots.txt before any scraping
- Check site's Terms of Service for scraping prohibitions
- Implement a Legitimate Interest Assessment (LIA) framework
- Add prominent legal warnings in CLI output when scraping restricted sites
- Never scrape EU personal data without documented lawful basis

**Warning signs:**
- No robots.txt parsing in codebase
- ToS checks missing from crawl logic
- User-agent not identifying the tool
- No GDPR/privacy consideration for email collection

**Phase to address:**
Foundation Phase — Legal compliance must be baked in from day one, not retrofitted.

---

### Pitfall 2: Unverified/Stale Email Data

**What goes wrong:**
Collected emails bounce, damaging sender reputation. Industry data shows 22-30% of B2B contact data decays annually. Tools that return "possible" emails without SMTP verification create bounce rates of 5-20%.

**Why it happens:**
Email finders often use pattern guessing (first.last@company.com) without real-time server verification. Catch-all domains accept all addresses, making validation unreliable without direct SMTP checks.

**How to avoid:**
- Integrate real-time SMTP verification before returning results
- Flag catch-all domains separately (don't treat as "verified")
- Remove role-based addresses (info@, admin@, support@) from results
- Never export emails that haven't passed verification
- Implement confidence scoring (only return 85%+ confidence results)

**Warning signs:**
- Export includes emails without verification status
- No distinction between "verified" and "possible" emails
- No catch-all domain detection
- High bounce rates reported by users

**Phase to address:**
Foundation Phase — Email verification is table stakes, not an afterthought.

---

### Pitfall 3: Aggressive Rate Limiting Violations

**What goes wrong:**
IP gets blocked by target sites. Tool becomes unusable because all sources block requests. For CLI tools with a small user base, even moderate request volumes trigger blocks.

**Why it happens:**
Developers optimize for speed, ignoring crawl-delay directives. Sites implement increasingly aggressive anti-bot measures. One aggressive run can get a residential IP blocked for days.

**How to avoid:**
- Respect crawl-delay directives from robots.txt (default to 10-15 second delays)
- Implement exponential backoff on 429 responses
- Use random delays between requests (not fixed intervals)
- Rotate user-agents to avoid pattern detection
- Implement request queuing with configurable rate limits
- Set conservative defaults (user can override)

**Warning signs:**
- No rate limiting configuration options
- Fixed delay between all requests
- No retry logic with backoff
- No robots.txt crawl-delay parsing

**Phase to address:**
Foundation Phase — Rate limiting is core functionality, not an add-on.

---

### Pitfall 4: Poor Data Quality - Garbage In, Garbage Out

**What goes wrong:**
Exported leads have incomplete data, wrong formats, or missing fields. Users spend hours cleaning data instead of doing outreach. Leads with missing phone numbers or incomplete contact info waste follow-up time.

**Why it happens:**
Scrapers extract what's available without validation. No schema enforcement. Missing fields aren't flagged. Data transforms without error handling.

**How to avoid:**
- Define strict schema for lead data (required vs optional fields)
- Implement validation at extraction time
- Flag leads with missing required fields
- Validate email formats, phone formats before export
- Add data completeness scores to output
- Never export leads below minimum quality threshold

**Warning signs:**
- No schema definition for lead data
- Missing field validation
- All extracted data exported without quality checks
- No "completeness score" in output

**Phase to address:**
Foundation Phase — Data quality gates prevent bad data from reaching users.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip email verification | Faster collection | Bounced emails destroy sender reputation | Never |
| Hard-code rate limits | Simpler code | Gets blocked on any scale | MVP only |
| Skip robots.txt parsing | Faster to ship | Legal risk, blocked sources | Never |
| Store credentials in code | Quick setup | Security breach, leaked keys | Never |
| Single-source scraping | Simpler architecture | Missing data, fragile | Only for MVP |
| No error recovery | Less code | Lost progress, incomplete exports | Never |
| Export all scraped data | More leads | Users overwhelmed, bad data | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Google Maps/Local | Ignoring ToS, scraping maps directly | Use official Places API where available |
| LinkedIn | Automated profile scraping | Respect rate limits, use Sales Navigator API |
| Website contact forms | Extracting without permission | Only collect publicly displayed data |
| Business directories | Assuming public = scrapable | Check ToS, respect restrictions |
| Social links | Following and scraping | Only collect URL, don't crawl deeper |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Memory accumulation | Tool slows, crashes on large lists | Stream processing, batch writes | > 10K leads |
| Sequential scraping | Hours to collect small list | Concurrent requests with rate limiting | > 100 URLs |
| No caching | Repeated scraping same sites | Cache robots.txt, site metadata | Multiple runs on same targets |
| Unbounded pagination | Never completes, infinite loop | Max page limits, cursor tracking | Sites with infinite scroll |
| DOM-dependent selectors | Breaks when site updates | Abstract selectors, fallback logic | Any site redesign |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Hardcoded API keys | Credentials exposed in repo | Environment variables, .env files |
| No HTTPS enforcement | Data intercepted in transit | Force TLS, warn on HTTP |
| Storing passwords | Password database vulnerable | Never store, use OAuth/token auth |
| Log output contains PII | Privacy violation | Sanitize logs, never log emails |
| CSV injection | Malicious formulas in export | Escape cells, prefix with apostrophe |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No progress indication | User thinks tool hung | Progress bars, ETA estimates |
| Silent failures | Missing data without warning | Explicit error messages per lead |
| One-size output | Rigid CSV that doesn't fit workflows | Configurable export formats |
| No undo/retry | Corrupted export requires restart | Checkpoint saves, resume capability |
| Cryptic errors | User can't diagnose problems | Human-readable error messages |
| No dry-run mode | User can't test without consequences | Preview mode before execution |

---

## "Looks Done But Isn't" Checklist

- [ ] **Email collection:** Verified emails with SMTP check — not just pattern-matched formats
- [ ] **Rate limiting:** Respects robots.txt crawl-delay — not just a fixed delay
- [ ] **Data export:** Only complete leads — not all scraped data regardless of quality
- [ ] **Legal compliance:** robots.txt parsed — not ignored "for speed"
- [ ] **Error recovery:** Checkpoint system — not lost progress on failure
- [ ] **GDPR handling:** Privacy warnings — not silent collection of EU data
- [ ] **Source attribution:** Each lead tagged with source — not anonymous exports
- [ ] **Bounce protection:** Verification before export — not raw email delivery

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|---------------|
| IP blocked | MEDIUM | Switch to proxy rotation, wait 24-48hrs, reduce rate |
| Bad data exported | HIGH | Add verification layer, re-verify before resend |
| Legal complaint | VERY HIGH | Remove data, document compliance measures, consult counsel |
| Bounced campaign | MEDIUM | Re-verify all emails, remove bounces, warm up sender |
| Source site changed | LOW | Update selectors, implement monitoring alerts |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Legal non-compliance | Foundation | robots.txt parser exists, ToS warnings in output |
| Unverified email data | Foundation | All exports show verification status |
| Rate limiting violations | Foundation | Rate limit config exposed, crawl-delay parsed |
| Poor data quality | Foundation | Schema validation runs, completeness scores shown |
| Performance traps | Foundation | Handles 10K+ leads without memory issues |
| Security mistakes | Foundation | No credentials in code, env vars used |
| UX pitfalls | Foundation | Progress shown, errors readable, dry-run works |
| GDPR violations | Foundation | Privacy warnings, data minimization in output |

---

## Sources

- [ScrapeGraphAI: Common Web Scraping Mistakes](https://www.scrapegraphai.com/blog/common-errors) — Scraping best practices
- [Medium: Web Scraping GDPR €20M Mistake](https://medium.com/deep-tech-insights/web-scraping-in-2025-the-20-million-gdpr-mistake-you-cant-afford-to-make-07a3ce240f4f) — Legal compliance
- [Lead411: Why B2B Data Is Bad](https://www.lead411.com/sales-and-marketing/our-data-sucks/) — Data decay statistics
- [Clearout: Why Email Finders Return Inaccurate Emails](https://clearout.io/blog/why-email-finders-return-inaccurate-emails/) — Email accuracy
- [Instantly: Cold Email Software Mistakes](https://instantly.ai/blog/cold-email-software-mistakes-to-avoid-12-costly-errors-that-tank-deliverability-roi/) — Deliverability

---
*Pitfalls research for: B2B Lead Generation CLI Tool*
*Researched: 2026-04-03*
