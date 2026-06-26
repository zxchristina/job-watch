# Job Watch

A personal job discovery tool that automatically finds new Bay Area data / analyst / AI job postings from company career pages, filters them by fit, and tracks application status — all running locally on macOS with no scraping and no third-party job boards.

## What it does

Twice a day (8:30 AM and 3:30 PM), Job Watch:

1. **Polls 300+ company career boards** directly via public ATS APIs (Greenhouse, Lever, Ashby, Workday) — no Google, no LinkedIn, no scraping
2. **Filters** by title, location (SF Bay Area + US remote only), seniority level, and years-of-experience requirement parsed from the job description
3. **Flags** postings that explicitly say they won't sponsor visas
4. **Drops stale postings** older than 2 weeks — Bay Area tech roles move fast
5. **Deduplicates** against a persistent tracker so already-seen jobs never resurface
6. **Serves a live HTML report** at `http://localhost:8765` grouped by role family and freshness tier
7. **Sends an email digest** with the same structure as a backup
8. **Fires a macOS notification** so you know when new jobs are ready to review

Status buttons (Applied / Referred / Pass) update the tracker in real time — no spreadsheet editing needed.

## Architecture

```
runner.py          # orchestrates each run; argparse CLI
├── discover.py    # auto-resolves bare company names → ATS board URLs (cached)
├── hn_discover.py # extracts company names from HN "Who is Hiring?" threads
├── fetchers.py    # per-ATS fetch + normalize (Greenhouse / Lever / Ashby / Workday)
├── filters.py     # title, location, YOE, sponsorship, freshness checks
├── scorer.py      # relevance score based on skills in JD
├── tracker.py     # persistent CSV; add-only, never overwrites manual edits
├── report.py      # generates report.html + manages local server lifecycle
├── emailer.py     # Gmail SMTP digest (port 587 STARTTLS)
└── server.py      # lightweight HTTP server; serves report + /mark + /tracker endpoints
companies.py       # registry of 116 verified ATS URLs + 201 auto-discover names
```

## Key design decisions

**Direct ATS API polling** — Each ATS (Greenhouse, Lever, Ashby) exposes a public JSON endpoint per company board. Polling these directly is fast, structured, and reliable compared to scraping rendered HTML.

**DISCOVER mode** — For companies where the exact board URL isn't known, the resolver generates slug candidates (`"dbt Labs"` → `dbtlabs`, `dbt-labs`, `dbt`) and probes each ATS. Hits and misses are both cached so each company is probed at most once.

**HN "Who is Hiring?" integration** — Monthly Hacker News hiring threads surface companies too new or niche to know by name. The tool parses the latest thread via the public Algolia HN API, extracts company names, and feeds them into the DISCOVER resolver. Up to 80 new companies are probed per run; the full thread is covered over a few days.

**Allowlist location filter** — Rather than blocking known non-Bay-Area cities, the filter explicitly keeps only Bay Area cities and US-remote postings. Anything unrecognized is dropped. This prevents international offices or obscure city names from slipping through.

**Tracker-first dedup** — `tracker.csv` is keyed by `company::job_id`. Each run only adds genuinely new rows; manual status edits (`applied`, `referred`, `rejected`) are never overwritten. Jobs marked anything other than `new` never resurface in the report.

**No Flask, no database** — The server is Python's built-in `http.server`. The tracker is a CSV. The entire tool runs with standard library only (plus `requests` for HTTP).

## Filtering rules

| Filter | Rule |
|--------|------|
| Title | Keep: data scientist, data/analytics engineer, ML/AI engineer, applied scientist, analyst variants (people analytics, pricing, fraud, growth, insights, GTM, etc.) |
| Seniority | Drop: senior, staff, principal, director, VP, lead, manager, head of |
| Level | Drop: intern / internship |
| YOE | Drop if minimum required ≥ 5 years (parsed from JD text) |
| Location | Keep: SF Bay Area cities + US remote; drop everything else |
| Staleness | Drop postings older than 14 days |
| Sponsorship | Flag (don't drop) JDs that say they won't sponsor visas |

## Freshness tiers

Jobs are grouped and sorted by how recently they were posted:

| Tier | Priority |
|------|----------|
| < 1 hour | Act immediately |
| < 24 hours | Today's picks — shown in a dedicated section at the top |
| < 48 hours | Still very fresh |
| < 72 hours | Posted this week |
| < 1 week | Worth reviewing |
| < 2 weeks | Oldest shown |

## Setup

```bash
# Clone and enter the project
git clone https://github.com/zxchristina/job-watch.git
cd job-watch

# No pip install needed — standard library only
# (Add your Gmail app password to email_config.py — see email_config.example.py)

# Run once manually
python runner.py

# Or skip the discovery step if you've run before
python runner.py --no-discover --window 24h
```

Open `http://localhost:8765` to see the report. The server starts automatically on first run.

## Automated scheduling (macOS)

The tool ships with two launchd plist files that run it at **8:30 AM** and **3:30 PM** daily:

```bash
# Load the scheduler (run once)
launchctl load ~/Library/LaunchAgents/com.jobwatch.runner.plist
launchctl load ~/Library/LaunchAgents/com.jobwatch.server.plist
```

## Company coverage

- **116 verified** companies with known ATS board URLs (Databricks, Stripe, OpenAI, Anthropic, Airbnb, Lyft, Ramp, Notion, Figma, and more)
- **201 auto-discover** companies probed on first run and cached
- **3 Workday** companies (Adobe, Nvidia, Salesforce)
- **HN "Who is Hiring?"** thread parsed monthly for additional unknown companies

## Tech stack

Python 3 · standard library only · macOS launchd · Gmail SMTP · Greenhouse / Lever / Ashby / Workday APIs · Algolia HN API
