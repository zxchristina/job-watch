# scorer.py — relevance scoring (0–10 scale)
#
# Points breakdown:
#   Title quality  : 0–4  (how well the title matches your target roles)
#   Skills in JD   : 0–4  (how many of your key skills appear in the description)
#   Freshness bonus: 0–2  (newer postings ranked slightly higher)

import re
from companies import SKILLS
from filters import freshness_tier

_STRIP_HTML = re.compile(r"<[^>]+>")


def score(job):
    title = job.get("title", "").lower()
    desc  = _STRIP_HTML.sub(" ", job.get("description", "") or "").lower()

    # ── Title score ───────────────────────────────────────────────────────────
    if any(x in title for x in ["data scientist", "decision scientist", "analytics scientist",
                                  "quantitative analyst", "quant analyst"]):
        title_score = 4
    elif any(x in title for x in ["analytics engineer"]):
        title_score = 4
    elif any(x in title for x in ["data engineer"]):
        title_score = 3
    elif any(x in title for x in ["ml engineer", "machine learning engineer", "ai engineer",
                                    "applied scientist", "applied ml", "research engineer"]):
        title_score = 3
    elif "analyst" in title:
        title_score = 2
    else:
        title_score = 1

    # ── Skills score (cap at 4) ───────────────────────────────────────────────
    skill_hits = sum(1 for s in SKILLS if s in desc)
    skill_score = min(skill_hits, 4)

    # ── Freshness bonus ───────────────────────────────────────────────────────
    _, tier_key = freshness_tier(job.get("posted_at"))
    # tier 0 (< 1hr) or 1 (< 24hr) → +2; tier 2-3 → +1; older → +0
    freshness_score = 2 if tier_key <= 1 else (1 if tier_key <= 3 else 0)

    return min(title_score + skill_score + freshness_score, 10)
