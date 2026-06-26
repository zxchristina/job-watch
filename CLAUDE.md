# Job Watch — project brief

## What this project is
A personal, locally-run tool that automatically **discovers** new Bay Area data / analyst / AI job
postings from company career boards, filters and ranks them by fit, and tracks which ones I've
applied to. It does **discovery and triage only — never auto-applies.** I apply manually so I can
add a referral and tailor each application.

## Who it's for
Christina — targeting mid-level Data Scientist / Data Engineer / Analytics Engineer / Analyst /
AI-ML roles in the SF Bay Area. ~2 years experience + M.S. Business Analytics. **Requires H-1B
visa sponsorship** (F-1 STEM OPT → H-1B change of status), so sponsorship signals matter.

## How it works (already prototyped in Python)
Polls public ATS JSON endpoints directly — no scraping, no Google:
- **Greenhouse**: `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true`
- **Lever**: `https://api.lever.co/v0/postings/{slug}?mode=json`
- **Ashby**: `https://api.ashbyhq.com/posting-api/job-board/{slug}`
- **SmartRecruiters**: `https://api.smartrecruiters.com/v1/companies/{slug}/postings`
- **Workday**: POST `https://{host}/wday/cxs/{tenant}/{site}/jobs`

The board URL encodes the ATS + slug, so a company is just `("Name", "https://boards.greenhouse.io/databricks")`.
There's also a **DISCOVER** mode: given a bare company name, probe candidate slugs across
Greenhouse/Lever/Ashby and cache what resolves.

## Filtering & scoring rules
- **Titles to keep**: data scientist, data engineer, analytics engineer, ML/AI engineer, applied
  scientist, plus analyst variants (data/business/BI/product/people analytics/operations/marketing).
- **Drop**: titles containing intern/internship; senior/staff/principal/director/VP/head.
- **Drop 5+ YOE**: parse the job description for minimum years-of-experience; drop if the minimum
  required is >= 5 (a "3–5 years" role is kept — I clear the low end).
- **Location**: keep Bay Area cities + US-remote; drop EMEA/APAC/India/Canada remote.
- **Relevance score**: title match + skills present in JD (dbt, Snowflake, SQL, experimentation,
  causal inference, LLM eval, Airflow, etc.). Sort newest-first within each role family.
- **Sponsorship flag**: mark (don't drop) JDs that say they won't sponsor.

## Tracker (the important part)
A persistent CSV (`tracker.csv`) keyed by `company::job_id` with a `status` column
(new / applied / referred / rejected). Each run:
- adds only genuinely new postings as `status=new`
- **never re-shows or duplicates** a job already in the tracker
- preserves my manual status edits (so applied jobs don't resurface)

## Freshness & timing (critical)
Jobs are sorted and filtered by how recently they were posted. Priority tiers:
- Past 1 hour (best)
- Past 24 hours
- Past 48 hours
- Past 72 hours
- Past 1 week
- Up to 2 weeks (oldest we show)
- **Stale = older than 2 weeks — drop entirely.** After 2 weeks Bay Area tech roles are usually
  filled or dead.

Within each role family, sort newest-first.

## Automated schedule
Run **twice daily via macOS launchd** — not cron, launchd is more reliable on Mac.
- **8:30am PT** — catches overnight + early-morning posts before the day starts
- **3:30pm PT** — catches the full morning wave (peak posting time is Tue–Thu 9–11am + 1–3pm)

The tracker.csv handles persistence across runs: jobs you've applied to won't resurface.

## Output
Group by role family (Data Scientist / Data Engineer / Analytics Engineer / ML-AI / Analyst),
newest-first, each row showing: title, company, location, posted date/age, relevance score,
min-YOE, sponsorship flag, and apply link.

## Roadmap (what I want to build next, in order)
1. Turn the prototype into a clean local project (modules, not one giant script).
2. **Applied-tracking**: robust dedupe + status preservation as above.
3. **5+ YOE filter**: reliable JD parsing for minimum experience.
4. **Better DISCOVER coverage**: the auto-resolver currently misses too many companies — improve
   slug-candidate generation and caching; let me feed a big list of company names.
5. **Freshness filter**: enforce the 2-week staleness cutoff; sort by posted date within families.
6. **Automated twice-daily runs** via macOS launchd at 8:30am and 3:30pm PT.

## Constraints / preferences
- Python, standard library preferred; minimal dependencies.
- Must run locally on macOS. No scraping of Google or LinkedIn.
- Keep it simple and readable — I'm not a software engineer, I'll be reading this code.
- Explain what you're doing in plain English as you go.

## My working style with you
I chat in plain English; you write and run the code. Ask me for the inputs you need (like my list
of target companies) rather than guessing. Show me results, and I'll steer.
