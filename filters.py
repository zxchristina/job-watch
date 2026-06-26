# filters.py — title, location, YOE, sponsorship, freshness checks

import re
from datetime import datetime, timezone
from companies import INCLUDE_TITLE, EXCLUDE_TITLE, SENIOR_TITLE, BAY_AREA


def title_ok(title):
    """Return True if the title is a role we want and not excluded/senior."""
    t = title.lower()
    if any(x in t for x in EXCLUDE_TITLE):
        return False
    if any(x in t for x in SENIOR_TITLE):
        return False
    return any(x in t for x in INCLUDE_TITLE)


def location_ok(location):
    """
    Keep Bay Area cities and US-remote. Drop everything else.
    Empty/unknown location is kept (can't tell, so don't penalize).
    """
    loc = location.lower()
    if not loc:
        return True

    # International signals → always drop
    intl = [
        # Regions
        "emea", "apac",
        # Countries
        "india", "canada", "mexico", "united kingdom", "germany", "france",
        "netherlands", "australia", "singapore", "japan", "brazil", "ireland",
        "israel", "poland", "spain", "sweden", "switzerland", "china", "korea",
        # Cities
        "london", "berlin", "paris", "amsterdam", "toronto", "vancouver",
        "sydney", "bangalore", "mumbai", "delhi", "mexico city", "tel aviv",
        "dublin", "warsaw", "stockholm", "zurich", "tokyo", "seoul",
        # Shorthand that appears in Greenhouse/Lever
        " uk", "uk ", "remote - uk", "remote - canada", "remote - europe",
        "remote - india", "remote - mexico", "remote, canada", "remote, uk",
        "remote, europe", "remote, india",
    ]
    if any(x in loc for x in intl):
        return False

    # Bay Area city → keep
    if any(x in loc for x in BAY_AREA):
        return True

    # US remote → keep (can be worked from Bay Area, no relocation needed)
    if "remote" in loc:
        return True

    # Everything else (other US cities, unrecognized) → drop
    # Christina is Bay Area-based and not relocating
    return False


_STRIP_HTML = re.compile(r"<[^>]+>")

def _clean(text):
    """Strip HTML tags and collapse whitespace."""
    return _STRIP_HTML.sub(" ", text or "").lower()


def parse_min_yoe(description):
    """
    Return the minimum years-of-experience integer required, or None if not found.

    Handles patterns like:
      "3+ years of experience"
      "3-5 years"
      "at least 2 years"
      "minimum 4 years"
      "2 to 4 years of relevant experience"
    """
    text = _clean(description)
    patterns = [
        # "3+" or "3-5" or "3–5" years (of) experience
        r"(\d+)\s*[+\-–]\s*\d*\s*years?\s*(?:of\s+)?(?:relevant\s+)?(?:experience|exp\b)",
        # "3+" years alone
        r"(\d+)\s*\+\s*years?\s*(?:of\s+)?(?:relevant\s+)?(?:experience|exp\b)",
        # "at least / minimum (of) N years"
        r"(?:at least|minimum\s+of?|minimum|min\.?)\s+(\d+)\s*years?",
        # "N to M years of experience"
        r"(\d+)\s+to\s+\d+\s+years?\s*(?:of\s+)?(?:relevant\s+)?(?:experience|exp\b)",
        # bare "N years of experience"
        r"(\d+)\s+years?\s+of\s+(?:relevant\s+)?(?:experience|exp\b)",
    ]
    found = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            val = int(m.group(1))
            if 0 < val < 20:   # sanity-check: ignore "20 years" or "0 years"
                found.append(val)
    return min(found) if found else None


def sponsorship_unwilling(description):
    """Return True if the JD explicitly says they will NOT sponsor visas."""
    text = _clean(description)
    signals = [
        "not able to sponsor", "unable to sponsor", "cannot sponsor",
        "does not sponsor", "will not sponsor", "no sponsorship",
        "sponsorship not available", "not eligible to sponsor",
        "visa sponsorship is not", "sponsorship is not provided",
        "we do not offer visa", "not provide sponsorship",
    ]
    return any(s in text for s in signals)


def is_stale(posted_at, cutoff_days=14):
    """Return True if the posting is older than cutoff_days."""
    if posted_at is None:
        return False   # unknown age: keep and let user decide
    now = datetime.now(tz=timezone.utc)
    p = posted_at if posted_at.tzinfo else posted_at.replace(tzinfo=timezone.utc)
    return (now - p).days > cutoff_days


# Freshness tiers in display order (newest first)
_TIERS = [
    (1,    "< 1 hour"),
    (24,   "< 24 hours"),
    (48,   "< 48 hours"),
    (72,   "< 72 hours"),
    (168,  "< 1 week"),
    (336,  "< 2 weeks"),
]

def freshness_tier(posted_at):
    """
    Return (label: str, sort_key: int).
    sort_key 0 = newest. Use ascending sort on sort_key to get newest-first.
    """
    if posted_at is None:
        return "unknown", 99
    now = datetime.now(tz=timezone.utc)
    p = posted_at if posted_at.tzinfo else posted_at.replace(tzinfo=timezone.utc)
    hours = (now - p).total_seconds() / 3600
    for key, (max_hours, label) in enumerate(_TIERS):
        if hours <= max_hours:
            return label, key
    return "< 2 weeks", len(_TIERS) - 1


def role_family(title):
    """Map a job title to one of the five display families."""
    t = title.lower()
    if any(x in t for x in ["ml engineer", "machine learning engineer", "ai engineer",
                              "applied scientist", "applied ml", "research engineer"]):
        return "ML / AI"
    if "analytics engineer" in t:
        return "Analytics Engineer"
    if any(x in t for x in ["data scientist", "decision scientist", "analytics scientist",
                              "quantitative analyst", "quant analyst"]):
        return "Data Scientist"
    if "data engineer" in t:
        return "Data Engineer"
    return "Analyst"
