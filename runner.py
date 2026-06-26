#!/usr/bin/env python3
# runner.py — Job Watch main entry point
#
# Usage:
#   python runner.py                   # fetch everything, show new jobs (2-week window)
#   python runner.py --window 24h      # only show jobs posted in last 24 hours
#   python runner.py --window 1h       # past hour only
#   python runner.py --discover-only   # just resolve DISCOVER names, don't fetch/report
#   python runner.py --no-discover     # skip DISCOVER step (faster, uses cache only)
#
# Window options: 1h | 24h | 48h | 72h | 1w | 2w (default: 2w)

import argparse
from datetime import datetime, timezone

import companies as cfg
import fetchers
import filters
import scorer
import tracker
import discover
import hn_discover
import report
import emailer


WINDOW_HOURS = {"1h": 1, "24h": 24, "48h": 48, "72h": 72, "1w": 168, "2w": 336}
ROLE_ORDER = ["Data Scientist", "Data Engineer", "Analytics Engineer", "ML / AI", "Analyst"]


def main():
    parser = argparse.ArgumentParser(description="Job Watch — find new job postings")
    parser.add_argument("--window",        default="2w", choices=WINDOW_HOURS,
                        help="Only show jobs posted within this window (default: 2w)")
    parser.add_argument("--discover-only", action="store_true",
                        help="Just run DISCOVER resolution and exit")
    parser.add_argument("--no-discover",   action="store_true",
                        help="Skip DISCOVER step (use cached results only)")
    parser.add_argument("--no-hn",         action="store_true",
                        help="Skip HN 'Who is Hiring?' discovery")
    args = parser.parse_args()

    now = datetime.now(tz=timezone.utc)
    cutoff_hours = WINDOW_HOURS[args.window]

    # ── Step 1: resolve DISCOVER companies ───────────────────────────────────
    if args.no_discover:
        # Use only what's already in the cache — no new probes
        import json, os
        cache = json.load(open(discover.CACHE_FILE)) if os.path.exists(discover.CACHE_FILE) else {}
        resolved = [(name, url) for name, url in cache.items() if url]
        print(f"[discover] Using cache: {len(resolved)} resolved companies (--no-discover)")
    else:
        print(f"\n{'='*60}")
        print(f"STEP 1 — Resolving {len(cfg.DISCOVER)} DISCOVER companies")
        print(f"{'='*60}")

        # ── Step 1b: HN "Who is Hiring?" discovery ───────────────────────────
        hn_extras = []
        if not args.no_hn:
            print(f"\n  [hn] Fetching company names from HN 'Who is Hiring?'...")
            hn_names = hn_discover.fetch_companies()
            hn_extras = hn_discover.pick_batch(
                hn_names, discover.CACHE_FILE, cfg.DISCOVER
            )

        all_names = list(cfg.DISCOVER) + hn_extras
        resolved = discover.resolve_all(all_names)
        print(f"Resolved {len(resolved)}/{len(all_names)} companies "
              f"({len(cfg.DISCOVER)} hardcoded + {len(hn_extras)} from HN)")

    if args.discover_only:
        return

    # ── Step 2: build full board list ────────────────────────────────────────
    all_boards = list(cfg.VERIFIED) + resolved

    print(f"\n{'='*60}")
    print(f"STEP 2 — Fetching {len(all_boards)} boards + {len(cfg.WORKDAY)} Workday")
    print(f"{'='*60}")

    raw_jobs = []
    for company, url in all_boards:
        print(f"  {company:<30}", end=" ", flush=True)
        jobs = fetchers.fetch(company, url)
        print(f"{len(jobs):>3} jobs")
        raw_jobs.extend(jobs)

    for company, url in cfg.WORKDAY:
        print(f"  {company:<30} (Workday)", end=" ", flush=True)
        jobs = fetchers.fetch(company, url)
        print(f"{len(jobs):>3} jobs")
        raw_jobs.extend(jobs)

    print(f"\nFetched {len(raw_jobs)} raw jobs total")

    # ── Step 3: filter ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"STEP 3 — Filtering")
    print(f"{'='*60}")

    kept = []
    dropped = {"title": 0, "location": 0, "stale": 0, "yoe": 0, "window": 0}

    for job in raw_jobs:
        if not filters.title_ok(job["title"]):
            dropped["title"] += 1;    continue
        if not filters.location_ok(job["location"]):
            dropped["location"] += 1; continue
        if filters.is_stale(job.get("posted_at"), cutoff_days=14):
            dropped["stale"] += 1;    continue

        min_yoe = filters.parse_min_yoe(job.get("description", ""))
        if min_yoe is not None and min_yoe >= 5:
            dropped["yoe"] += 1;      continue

        # Time-window filter (tighter than the 2-week staleness cutoff)
        posted = job.get("posted_at")
        if posted:
            p = posted if posted.tzinfo else posted.replace(tzinfo=timezone.utc)
            age_hours = (now - p).total_seconds() / 3600
            if age_hours > cutoff_hours:
                dropped["window"] += 1; continue

        # Enrich surviving jobs
        freshness, tier = filters.freshness_tier(posted)
        job["min_yoe"]        = min_yoe
        job["no_sponsorship"] = filters.sponsorship_unwilling(job.get("description", ""))
        job["role_family"]    = filters.role_family(job["title"])
        job["freshness"]      = freshness
        job["freshness_tier"] = tier
        job["score"]          = scorer.score(job)
        kept.append(job)

    print(f"  Dropped — title: {dropped['title']}  location: {dropped['location']}  "
          f"stale: {dropped['stale']}  5+YOE: {dropped['yoe']}  window: {dropped['window']}")
    print(f"  Kept: {len(kept)} jobs")

    # ── Step 4: dedupe against tracker ───────────────────────────────────────
    current_tracker, new_count = tracker.add_new_jobs(kept)
    already_tracked = len(kept) - new_count
    print(f"  New this run: {new_count}  |  Already tracked: {already_tracked}")

    # ── Step 5: report — only show status=new jobs ───────────────────────────
    new_jobs = [
        j for j in kept
        if current_tracker.get(
            tracker.make_key(j["company"], j["job_id"]), {}
        ).get("status") == "new"
    ]

    # ── Step 6: HTML report + notification + email ───────────────────────────
    report_path = report.generate(new_jobs, run_time=now, window=args.window)
    report.notify(new_count, report_path, reviewable=len(new_jobs))
    emailer.send(new_jobs, run_time=now, window=args.window)

    if not new_jobs:
        print(f"\nNo new jobs in the past {args.window}. Check back soon!")
        return

    print(f"\n{'='*70}")
    print(f"  JOB WATCH — {now.strftime('%Y-%m-%d %H:%M UTC')}  |  window: {args.window}  |  {new_count} new")
    print(f"{'='*70}")

    for family in ROLE_ORDER:
        family_jobs = [j for j in new_jobs if j["role_family"] == family]
        if not family_jobs:
            continue

        # Newest first, then by score descending
        family_jobs.sort(key=lambda j: (j["freshness_tier"], -j["score"]))

        print(f"\n  ── {family.upper()} ({len(family_jobs)}) " + "─" * max(0, 50 - len(family)))
        header = f"  {'Title':<38} {'Company':<18} {'Age':<12} {'Sc':>3} {'YOE':>4} {'Visa':>5}"
        print(header)
        print("  " + "-" * 82)

        for j in family_jobs:
            title    = j["title"][:37]
            company  = j["company"][:17]
            age      = j["freshness"]
            sc       = j["score"]
            yoe      = str(j["min_yoe"]) if j["min_yoe"] is not None else "?"
            visa     = "NO " if j["no_sponsorship"] else "ok "
            print(f"  {title:<38} {company:<18} {age:<12} {sc:>3} {yoe:>4} {visa:>5}")
            print(f"    {j['url']}")

    print(f"\n{'='*70}")
    print("  Tip: open tracker.csv and set status → applied / referred / rejected")
    print("  to hide those jobs from future reports.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
