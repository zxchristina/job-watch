# fetchers.py — pulls raw job listings from each ATS API
#
# Every fetcher returns a list of normalized dicts:
#   { job_id, company, title, url, location, posted_at, description, source }
#
# posted_at is a timezone-aware datetime (UTC) or None if the ATS doesn't
# provide it. Callers must handle None gracefully.

import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone


def _get(url, timeout=15):
    """HTTP GET → parsed JSON, or None on any error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "job-watch/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"    [warn] GET {url[:80]}: {e}")
        return None


def _parse_iso(s):
    """Parse an ISO-8601 string to a UTC-aware datetime, or return None."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


# ── ATS fetchers ──────────────────────────────────────────────────────────────

def fetch_greenhouse(company, board_url):
    slug = board_url.rstrip("/").split("/")[-1]
    data = _get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    if not data:
        return []
    jobs = []
    for j in data.get("jobs", []):
        # Greenhouse gives updated_at but not always a published date; use it as a proxy
        posted = _parse_iso(j.get("updated_at") or j.get("first_published"))
        jobs.append({
            "job_id":      str(j.get("id", "")),
            "company":     company,
            "title":       j.get("title", ""),
            "url":         j.get("absolute_url", ""),
            "location":    j.get("location", {}).get("name", ""),
            "posted_at":   posted,
            "description": j.get("content", ""),
            "source":      "greenhouse",
        })
    return jobs


def fetch_lever(company, board_url):
    slug = board_url.rstrip("/").split("/")[-1]
    data = _get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if not data:
        return []
    jobs = []
    for j in data:
        ts = j.get("createdAt")
        posted = datetime.fromtimestamp(ts / 1000, tz=timezone.utc) if ts else None
        jobs.append({
            "job_id":      j.get("id", ""),
            "company":     company,
            "title":       j.get("text", ""),
            "url":         j.get("hostedUrl", ""),
            "location":    j.get("categories", {}).get("location", ""),
            "posted_at":   posted,
            "description": j.get("descriptionPlain", "") or j.get("description", ""),
            "source":      "lever",
        })
    return jobs


def fetch_ashby(company, board_url):
    slug = board_url.rstrip("/").split("/")[-1]
    data = _get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    if not data:
        return []
    jobs = []
    for j in data.get("jobs", []):
        posted = _parse_iso(j.get("publishedDate"))
        location = j.get("location") or j.get("locationName") or ""
        jobs.append({
            "job_id":      j.get("id", ""),
            "company":     company,
            "title":       j.get("title", ""),
            "url":         j.get("jobUrl", ""),
            "location":    location,
            "posted_at":   posted,
            "description": j.get("descriptionHtml", "") or j.get("descriptionPlain", ""),
            "source":      "ashby",
        })
    return jobs


def fetch_smartrecruiters(company, board_url):
    slug = board_url.rstrip("/").split("/")[-1]
    data = _get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings")
    if not data:
        return []
    jobs = []
    for j in data.get("content", []):
        posted = _parse_iso(j.get("releasedDate") or j.get("createDate"))
        loc = j.get("location", {})
        location = ", ".join(filter(None, [loc.get("city"), loc.get("region"), loc.get("country")]))
        desc = (j.get("jobAd") or {}).get("sections", {}).get("jobDescription", {}).get("text", "")
        jobs.append({
            "job_id":      j.get("id", ""),
            "company":     company,
            "title":       j.get("name", ""),
            "url":         j.get("ref", ""),
            "location":    location,
            "posted_at":   posted,
            "description": desc,
            "source":      "smartrecruiters",
        })
    return jobs


def fetch_workday(company, board_url):
    """
    Workday uses a POST endpoint. board_url format:
      https://{tenant}.wd5.myworkdayjobs.com/{site}
    We send a broad search for "data" to catch DS/DE/analyst roles.
    """
    m = re.match(r"https://([^/]+)/(.+)", board_url.rstrip("/"))
    if not m:
        print(f"    [warn] Workday: can't parse URL {board_url}")
        return []
    host, site = m.group(1), m.group(2)
    tenant = host.split(".")[0]
    api = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    payload = json.dumps({
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": "data analyst engineer scientist",
    }).encode()

    try:
        req = urllib.request.Request(
            api, data=payload, method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "job-watch/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"    [warn] Workday POST {api[:80]}: {e}")
        return []

    jobs = []
    for j in data.get("jobPostings", []):
        ext = j.get("externalPath", "")
        url = f"https://{host}{ext}" if ext else ""
        posted = _parse_iso(j.get("postedOn"))
        jobs.append({
            "job_id":      j.get("bulletFields", [""])[0] if j.get("bulletFields") else j.get("title", ""),
            "company":     company,
            "title":       j.get("title", ""),
            "url":         url,
            "location":    j.get("locationsText", ""),
            "posted_at":   posted,
            "description": j.get("jobDescription", ""),
            "source":      "workday",
        })
    return jobs


# ── Router ────────────────────────────────────────────────────────────────────

def _detect_ats(url):
    if "greenhouse.io" in url:  return "greenhouse"
    if "lever.co"      in url:  return "lever"
    if "ashbyhq.com"   in url:  return "ashby"
    if "smartrecruiters.com" in url: return "smartrecruiters"
    if "myworkdayjobs.com"   in url: return "workday"
    return None


def fetch(company, board_url):
    """Auto-detect ATS from URL and fetch all jobs for that company."""
    ats = _detect_ats(board_url)
    dispatch = {
        "greenhouse":      fetch_greenhouse,
        "lever":           fetch_lever,
        "ashby":           fetch_ashby,
        "smartrecruiters": fetch_smartrecruiters,
        "workday":         fetch_workday,
    }
    fn = dispatch.get(ats)
    if not fn:
        print(f"    [warn] Unknown ATS for {company}: {board_url}")
        return []
    return fn(company, board_url)
