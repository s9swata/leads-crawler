# Lead Generation CLI

A CLI tool for finding and extracting business contact information from free sources. Generate CSV files with emails, phone numbers, social media links, and more — ready for cold outreach.

## Installation

```bash
pipx install .
```

## Setup

1. **Initialize the database:**

```bash
lead-gen init
```

2. **Set your API keys** in `.env`:

```env
SERPER_API_KEY=your_key_here
```

Get a free Serper API key at https://serper.dev/

## Quick Start

```bash
# Search, scrape, and export in one batch job
lead-gen batch --categories gyms --locations "Pune" --target 100 -o pune_gyms.csv

# Manual search + scrape workflow
lead-gen search --query "restaurants" --location "Pune" --limit 20 --ingest
lead-gen scrape --url "https://example-restaurant.com"
lead-gen export -o leads.csv --filter-email
```

## Commands

### `search` — Find business leads

Search for businesses and optionally save them to the database for later scraping.

```bash
lead-gen search --query "gyms" --location "Pune" --limit 20 --ingest
lead-gen search --query "dentist" --location "Koregaon Park Pune" --limit 10 --ingest
lead-gen search --query "web development agency" --location "Bangalore" --limit 20 --ingest
```

| Option | Description |
|---|---|
| `--query` | Search term (required) |
| `--location` | City or area to search in |
| `--limit` | Max results (default: 10) |
| `--ingest` | Save results to database for scraping |
| `--dry-run` | Preview without executing |

### `scrape` — Extract contact info from a URL

```bash
lead-gen scrape --url "https://example.com" --format json
lead-gen scrape --url "https://example.com" --format text
```

### `batch` — Generate leads at scale

Runs search + scrape automatically across categories and locations.

```bash
lead-gen batch --categories gyms,salons --locations "Pune,Mumbai" --target 500 -o leads.csv
lead-gen batch --categories all --target 1000 -o all_leads.csv
lead-gen batch --categories gyms --locations "Pune" --target 100 --require-email-and-phone -o verified.csv
```

| Option | Description |
|---|---|
| `--categories` | Comma-separated categories (default: all) |
| `--locations` | Comma-separated cities (default: all 23 cities) |
| `--target` | Target leads with emails (default: 1000) |
| `-o, --output` | Output CSV path |
| `--delay` | Seconds between scrapes (default: 2.0) |
| `--search-limit` | Max search results per query (default: 10) |
| `--require-email-and-phone` | Only save leads with both email AND valid phone |

### `leads` — View and filter leads

```bash
lead-gen leads
lead-gen leads --filter-email --filter-phone
lead-gen leads --source batch --sort company_name
lead-gen leads --per-page 50 --page 2
```

### `export` — Export leads to CSV

```bash
lead-gen export -o leads.csv
lead-gen export -o leads.csv --filter-email --filter-phone
lead-gen export -o leads.csv --columns "company_name,email,phone,address,business_category"
```

## Batch Categories

Each category expands into multiple search queries automatically:

| Category | Search Queries |
|---|---|
| `restaurants` | restaurant, cafe, bistro, fine dining, pizza restaurant, italian restaurant, chinese restaurant, indian restaurant, bakery, coffee shop |
| `gyms` | gym, fitness center, yoga studio, crossfit, pilates studio, health club, boxing gym, dance studio |
| `salons` | salon, beauty salon, hair salon, spa, barber shop, nail salon, beauty parlor, wellness center |
| `clinics` | clinic, dental clinic, doctor, healthcare clinic, physiotherapy clinic, dermatology clinic, eye clinic, diagnostic center |
| `real_estate` | real estate agency, property dealer, real estate broker, property consultant, real estate developer, property management, real estate agent |
| `coaching` | coaching institute, tuition center, coaching classes, training center, education center, language school, test preparation, career coaching |

Use `--categories all` to search all 6 categories (48 search queries per location).

## Available Locations

23 Indian cities available by default:

Pune, Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Kolkata, Ahmedabad, Jaipur, Lucknow, Chandigarh, Noida, Gurgaon, Nagpur, Indore, Bhopal, Surat, Vadodara, Coimbatore, Kochi, Visakhapatnam, Dehradun, Goa

You can also pass any custom location string: `--locations "Koregaon Park Pune"` or `--locations "Whitefield Bangalore"`.

## Available CSV Columns

| Column | Description |
|---|---|
| `company_name` | Business name |
| `email` | Contact email address |
| `website` | Website URL |
| `phone` | Phone number |
| `linkedin` | LinkedIn profile URL |
| `address` | Business address |
| `business_category` | Category/industry |
| `source` | How the lead was found (search, scrape, batch) |
| `source_url` | Original URL where lead was discovered |
| `discovered_at` | When the lead was first found |
| `scraped_at` | When the website was scraped |

Default export columns: `company_name, email, website, phone, address, business_category, source, discovered_at`

## Typical Workflow

```bash
# 1. Batch generate leads for a category in one city
lead-gen batch --categories restaurants --locations "Pune" --target 200 -o pune_restaurants.csv

# 2. Export only leads with both email and phone
lead-gen export -o verified.csv --filter-email --filter-phone

# 3. View leads in terminal
lead-gen leads --filter-email --per-page 30
```
