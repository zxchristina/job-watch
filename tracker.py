# tracker.py — persistent application tracker (tracker.csv)
#
# Key  = "company::job_id"   — unique across all ATS
# Status values: new / applied / referred / rejected
#
# Rules:
#   - Each run adds genuinely new jobs as status=new
#   - Jobs already in the tracker are NEVER overwritten (preserves your edits)
#   - "new" jobs resurface in reports; others are silently skipped

import csv
import os
from datetime import datetime, timezone

TRACKER_FILE = "tracker.csv"

COLUMNS = [
    "key", "company", "job_id", "title", "url", "location",
    "posted_at", "relevance_score", "min_yoe", "no_sponsorship",
    "role_family", "freshness", "status", "seen_at",
]


def load():
    """Return the full tracker as a dict keyed by 'company::job_id'."""
    if not os.path.exists(TRACKER_FILE):
        return {}
    with open(TRACKER_FILE, newline="", encoding="utf-8") as f:
        return {row["key"]: row for row in csv.DictReader(f)}


def save(records: dict):
    """Write the entire tracker dict back to CSV."""
    with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records.values())


def make_key(company, job_id):
    return f"{company}::{job_id}"


def add_new_jobs(enriched_jobs):
    """
    Merge a list of enriched job dicts into tracker.csv.
    Only adds jobs whose key isn't already present.
    Returns (updated_tracker_dict, count_of_new_jobs_added).
    """
    tracker = load()
    now_str = datetime.now(tz=timezone.utc).isoformat()
    new_count = 0

    for job in enriched_jobs:
        key = make_key(job["company"], job["job_id"])
        if key in tracker:
            continue   # already tracked — don't touch it

        posted = job.get("posted_at")
        tracker[key] = {
            "key":             key,
            "company":         job["company"],
            "job_id":          job["job_id"],
            "title":           job["title"],
            "url":             job["url"],
            "location":        job["location"],
            "posted_at":       posted.isoformat() if posted else "",
            "relevance_score": job.get("score", 0),
            "min_yoe":         job.get("min_yoe") if job.get("min_yoe") is not None else "",
            "no_sponsorship":  "yes" if job.get("no_sponsorship") else "no",
            "role_family":     job.get("role_family", ""),
            "freshness":       job.get("freshness", ""),
            "status":          "new",
            "seen_at":         now_str,
        }
        new_count += 1

    if new_count:
        save(tracker)

    return tracker, new_count
