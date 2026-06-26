# discover.py — auto-resolves bare company names to ATS board URLs
#
# For each name in companies.DISCOVER, we generate slug candidates and probe
# Greenhouse / Lever / Ashby API endpoints. Results (hits AND misses) are
# cached in discover_cache.json so each company is only probed once.
#
# Cache entries:
#   { "company name": "https://..." }   → resolved board URL
#   { "company name": null }            → confirmed miss (skip next time)
#
# To force a re-probe, delete the company's entry from discover_cache.json.

import json
import os
import re
import urllib.request
import urllib.error

CACHE_FILE = "discover_cache.json"


def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True)


def _slug_candidates(name):
    """
    Generate URL slug guesses from a company name.
    E.g. "dbt Labs" → ["dbtlabs", "dbt-labs", "dbt"]
         "Weights & Biases" → ["weightsbiases", "weights-biases", "weights", "wandb"]
    """
    base = name.lower()
    base = re.sub(r"[^a-z0-9\s]", "", base).strip()   # drop & . , etc.
    words = base.split()

    slug_concat = "".join(words)                        # "dbtlabs"
    slug_dash   = "-".join(words)                       # "dbt-labs"
    slug_first  = words[0] if words else ""             # "dbt"

    # Known abbreviations / brand slugs that don't follow the pattern
    overrides = {
        "weights & biases":    ["wandb"],
        "weights and biases":  ["wandb"],
        "dbt labs":            ["dbtlabs", "dbt-labs"],
        "luma ai":             ["luma-ai", "lumaai"],
        "together ai":         ["togetherai", "together-ai"],
        "fireworks ai":        ["fireworksai", "fireworks-ai"],
        "contextual ai":       ["contextualai", "contextual-ai"],
        "snorkel ai":          ["snorkelai", "snorkel-ai"],
        "patronus ai":         ["patronusai", "patronus-ai"],
        "character.ai":        ["character", "characterai"],
        "hims & hers":         ["himsandhers", "hims-hers"],
        "cockroach labs":      ["cockroachlabs", "cockroach-labs"],
        "modern treasury":     ["moderntreasury", "modern-treasury"],
        "abnormal security":   ["abnormalsecurity", "abnormal-security"],
        "aurora solar":        ["aurorasolar", "aurora-solar"],
        "the realreal":        ["therealreal", "the-realreal"],
        "10x genomics":        ["10xgenomics", "10x-genomics"],
        "guardant health":     ["guardanthealth", "guardant-health"],
        "pacific biosciences": ["pacificbiosciences", "pacbio"],
        "mammoth biosciences": ["mammothbiosciences", "mammoth-biosciences"],
        "arcus biosciences":   ["arcusbiosciences", "arcus-biosciences"],
        "vir biotechnology":   ["virbiotechnology", "vir-bio", "virbio"],
        "twist bioscience":    ["twistbioscience", "twist-bioscience"],
        "arize ai":            ["arizeai", "arize-ai"],
        "fiddler ai":          ["fiddlerai", "fiddler-ai"],
        "culture amp":         ["cultureamp", "culture-amp"],
        "ixl learning":        ["ixllearning", "ixl-learning"],
        "la launch darkly":    ["launchdarkly", "launch-darkly"],
        "launchdarkly":        ["launchdarkly", "launch-darkly"],
        "ring central":        ["ringcentral", "ring-central"],
        "15five":              ["15five"],
        "pagerduty":           ["pagerduty", "pager-duty"],
    }
    extras = overrides.get(name.lower(), [])

    # Deduplicate while preserving order (most-specific first)
    seen, candidates = set(), []
    for s in extras + [slug_concat, slug_dash, slug_first]:
        if s and s not in seen:
            seen.add(s)
            candidates.append(s)
    return candidates


def _probe_url(url, timeout=8):
    """Return True if the URL responds with HTTP 200."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "job-watch/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def resolve(company_name):
    """
    Return the ATS board URL for company_name, or None if unresolvable.
    Result is cached in discover_cache.json.
    """
    cache = _load_cache()
    key = company_name.lower()

    if key in cache:
        return cache[key]   # may be None (confirmed miss — skip silently)

    for slug in _slug_candidates(company_name):
        probes = [
            ("greenhouse", f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
                           f"https://boards.greenhouse.io/{slug}"),
            ("lever",      f"https://api.lever.co/v0/postings/{slug}?mode=json",
                           f"https://jobs.lever.co/{slug}"),
            ("ashby",      f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                           f"https://jobs.ashbyhq.com/{slug}"),
        ]
        for ats, probe_url, board_url in probes:
            if _probe_url(probe_url):
                print(f"  [discover] {company_name} → {board_url}  ({ats})")
                cache[key] = board_url
                _save_cache(cache)
                return board_url

    # Nothing resolved — cache the miss so we don't probe again
    cache[key] = None
    _save_cache(cache)
    return None


def resolve_all(company_names, verbose=True):
    """
    Resolve a list of company names. Returns list of (name, board_url) tuples
    for only the ones that resolved successfully.
    """
    results = []
    for name in company_names:
        url = resolve(name)
        if url:
            results.append((name, url))
        elif verbose:
            pass   # miss already printed inside resolve()
    return results
