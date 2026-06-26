# hn_discover.py — extract company names from HN "Who is Hiring?" threads
#
# Every month Hacker News runs "Ask HN: Who is Hiring?" — hundreds of real
# job postings from companies you'd never find by guessing names. We pull
# company names from the latest thread and feed them into the DISCOVER
# resolver, which probes GH/Lever/Ashby for each one.
#
# Uses the public Algolia HN API (no key needed). Results are cached for
# CACHE_DAYS so we're not hammering the API on every run.
#
# Cache is capped: we only probe up to HN_BATCH_PER_RUN *new* companies
# per runner run. Already-cached names (hit or miss in discover_cache.json)
# are instant. Over many runs the full thread gets covered.

import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

CACHE_FILE    = "hn_companies.json"
CACHE_DAYS    = 7          # refresh the thread list weekly (new thread each month)
HN_BATCH_PER_RUN = 80     # max new companies to probe per run

_ALGOLIA_SEARCH = (
    "https://hn.algolia.com/api/v1/search_by_date"
    "?query=Ask+HN%3A+Who+is+Hiring"
    "&tags=ask_hn"
    "&hitsPerPage=10"
)
_STRIP_HTML = re.compile(r"<[^>]+>")

# Words that indicate the "company" field is actually a job title
_JOB_TITLE_WORDS = {
    "engineer", "engineers", "developer", "developers", "designer", "designers",
    "intern", "internship", "manager", "managers", "analyst", "analysts",
    "scientist", "researchers", "researcher", "architect", "director",
    "lead", "principal", "senior", "junior", "staff", "head", "vp", "cto", "ceo",
    "frontend", "backend", "fullstack", "devops", "sre", "hiring",
}


def _get(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "job-watch/1.0 (personal job tracker)"}
    )
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read())


def _latest_story_id():
    """Return the objectID of the most recent 'Who is Hiring?' story."""
    try:
        data = _get(_ALGOLIA_SEARCH)
    except Exception as e:
        print(f"  [hn] Algolia search failed: {e}")
        return None

    hits = [
        h for h in data.get("hits", [])
        if "who is hiring" in h.get("title", "").lower()
        and "freelancer" not in h.get("title", "").lower()
    ]
    if not hits:
        return None
    hits.sort(key=lambda h: h.get("created_at_i", 0), reverse=True)
    best = hits[0]
    print(f"  [hn] Latest thread: \"{best.get('title','')}\" ({best.get('created_at','')[:10]})")
    return best["objectID"]


def _extract_company(html):
    """
    Parse a company name from a pipe-delimited HN hiring comment.
    Most posts look like: "CompanyName | Role | Location | ..."
    Returns None if the first field looks like a job title rather than a company.
    """
    text = _STRIP_HTML.sub(" ", html or "").strip()
    first = re.split(r"[\n<]", text)[0].strip()

    # Only attempt extraction when the post uses a clear delimiter.
    # Without a pipe/dash, the free-form opener is usually a job title, not a company.
    if "|" in first:
        name = first.split("|")[0].strip()
    elif " – " in first or " — " in first:
        name = re.split(r" [–—] ", first)[0].strip()
    elif " - " in first:
        name = first.split(" - ")[0].strip()
    else:
        return None  # no clear delimiter → skip to avoid noise

    # Strip markdown / punctuation artifacts
    name = re.sub(r"[*_`~#\[\]]", "", name).strip()
    name = name.rstrip(".,;:!?").strip()
    # Drop parentheticals like "(YC W22)" or "(Series B)"
    name = re.sub(r"\(.*?\)", "", name).strip()
    # Drop bare URLs
    name = re.sub(r"https?://\S+", "", name).strip()

    # Skip if looks like a sentence opener
    starters = ("we ", "we're", "i ", "our ", "the ", "hi ", "hey ",
                 "looking ", "seeking ", "join ")
    if name.lower().startswith(starters):
        return None

    # Skip if the candidate reads like a job title
    words_lower = {w.strip("s") for w in name.lower().split()}
    if words_lower & _JOB_TITLE_WORDS:
        return None

    # Length sanity
    if not 2 <= len(name) <= 55:
        return None

    return name or None


def _fetch_thread_companies(story_id):
    """Fetch all top-level comments from a story and extract company names."""
    companies = []
    seen = set()
    for page in range(6):  # up to 6000 comments; real threads are ~600-900
        url = (
            f"https://hn.algolia.com/api/v1/search_by_date"
            f"?tags=comment,story_{story_id}&hitsPerPage=1000&page={page}"
        )
        try:
            data = _get(url)
        except Exception as e:
            print(f"  [hn] page {page} fetch failed: {e}")
            break

        hits = data.get("hits", [])
        if not hits:
            break

        for hit in hits:
            # Only top-level comments (direct children of the story)
            if str(hit.get("parent_id")) != str(story_id):
                continue
            name = _extract_company(hit.get("comment_text", ""))
            key = name.lower() if name else None
            if name and key not in seen:
                seen.add(key)
                companies.append(name)

        if len(hits) < 1000:
            break  # last page

    return companies


def fetch_companies(force=False):
    """
    Return a list of company names extracted from the latest HN thread.
    Results are cached for CACHE_DAYS days.
    """
    # Check cache
    if not force and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        try:
            age_days = (
                datetime.now(tz=timezone.utc)
                - datetime.fromisoformat(cache["fetched_at"])
            ).days
        except Exception:
            age_days = 999

        if age_days < CACHE_DAYS:
            names = cache.get("companies", [])
            print(f"  [hn] cache: {len(names)} companies ({age_days}d old, "
                  f"refreshes in {CACHE_DAYS - age_days}d)")
            return names

    story_id = _latest_story_id()
    if not story_id:
        print("  [hn] Could not find 'Who is Hiring?' post — skipping")
        return []

    companies = _fetch_thread_companies(story_id)
    print(f"  [hn] Extracted {len(companies)} unique company names from thread")

    cache = {
        "story_id":  story_id,
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "companies":  companies,
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

    return companies


def pick_batch(hn_companies, discover_cache_file, already_in_discover):
    """
    Return the subset of hn_companies to probe this run:
    - Skip names already probed (in discover_cache)
    - Skip names already in the hardcoded DISCOVER list
    - Cap at HN_BATCH_PER_RUN to keep runs fast
    """
    cache_keys = set()
    if os.path.exists(discover_cache_file):
        with open(discover_cache_file, encoding="utf-8") as f:
            cache_keys = set(json.load(f).keys())

    known = {n.lower() for n in already_in_discover} | cache_keys

    fresh = [n for n in hn_companies if n.lower() not in known]
    # Sort alphabetically for deterministic batching across runs
    fresh.sort(key=str.lower)
    batch = fresh[:HN_BATCH_PER_RUN]

    already_cached = len(hn_companies) - len(fresh)
    print(f"  [hn] {already_cached} already cached, {len(fresh)} new "
          f"→ probing {len(batch)} this run")
    return batch
