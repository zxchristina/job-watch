# report.py — generates report.html and fires a macOS notification
#
# Structure:
#   1. "Last 24 Hours" section — all roles, newest first (act on these first)
#   2. Role-family sections   — remaining jobs (24h–2w), newest first within each
#
# Each job row has Apply →, ✓ Applied, ↗ Referred, ✗ Pass buttons.
# Clicking a status button calls http://localhost:8765/mark and updates
# tracker.csv live — no CSV editing needed.

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from datetime import datetime, timezone

REPORT_FILE = "report.html"
SERVER_PORT = 8765
SERVER_URL  = f"http://localhost:{SERVER_PORT}"

_BADGE = {
    "< 1 hour":   ("#d4edda", "#155724"),
    "< 24 hours": ("#d4edda", "#155724"),
    "< 48 hours": ("#fff3cd", "#856404"),
    "< 72 hours": ("#fff3cd", "#856404"),
    "< 1 week":   ("#ffe5d0", "#7d3c00"),
    "< 2 weeks":  ("#e2e3e5", "#383d41"),
    "unknown":    ("#e2e3e5", "#383d41"),
}

FAMILY_ORDER = [
    "Data Scientist", "Data Engineer", "Analytics Engineer", "ML / AI", "Analyst"
]

_JS = """
<script>
function markJob(btn) {
  const row    = btn.closest('tr');
  const key    = row.dataset.key;
  const status = btn.dataset.status;
  const labels = {applied:'✓ Applied', referred:'↗ Referred', rejected:'✗ Passed'};
  const bgs    = {applied:'#d4edda',   referred:'#fff3cd',    rejected:'#f8d7da'};
  const fgs    = {applied:'#155724',   referred:'#856404',    rejected:'#721c24'};

  fetch(`/mark?key=${encodeURIComponent(key)}&status=${encodeURIComponent(status)}`)
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        row.querySelector('.row-actions').innerHTML =
          `<span style="background:${bgs[status]};color:${fgs[status]};` +
          `padding:3px 10px;border-radius:8px;font-size:12px;font-weight:600">` +
          `${labels[status]}</span>`;
        row.style.opacity = '0.45';
      }
    })
    .catch(() => alert('Server not reachable. Is server.py running?'));
}
</script>
"""

_BTN_STYLE = (
    "background:#f0f0f0;color:#333;border:none;padding:4px 9px;"
    "border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;margin:0 2px"
)


def _freshness_badge(label):
    bg, fg = _BADGE.get(label, ("#e2e3e5", "#383d41"))
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:12px;font-size:12px;font-weight:600;white-space:nowrap">'
            f'{label}</span>')


def _visa_tag(no_sponsorship):
    if no_sponsorship in ("yes", True):
        return ('<span style="background:#f8d7da;color:#721c24;padding:2px 8px;'
                'border-radius:12px;font-size:12px;font-weight:600">NO VISA</span>')
    return ('<span style="background:#d4edda;color:#155724;padding:2px 8px;'
            'border-radius:12px;font-size:12px;font-weight:600">visa ok</span>')


def _job_row(job, show_family=False):
    key       = f"{job.get('company','')}::{job.get('job_id','')}"
    freshness = job.get("freshness", "unknown")
    yoe       = job.get("min_yoe")
    yoe_str   = f"{yoe}+ yr" if yoe is not None else "?"
    url       = job.get("url", "#")

    family_tag = ""
    if show_family:
        family_tag = (
            f'<span style="background:#f0f0f0;color:#555;padding:1px 6px;'
            f'border-radius:8px;font-size:11px;margin-left:6px">'
            f'{job.get("role_family","")}</span>'
        )

    return f"""
    <tr data-key="{key}" style="border-bottom:1px solid #f0f0f0">
      <td style="padding:10px 8px;max-width:260px">
        <a href="{url}" target="_blank"
           style="color:#1a1a1a;font-weight:600;text-decoration:none;font-size:14px"
           onmouseover="this.style.color='#0066cc'" onmouseout="this.style.color='#1a1a1a'">
          {job.get("title","")}</a>{family_tag}<br>
        <span style="color:#555;font-size:13px">{job.get("company","")}</span>
      </td>
      <td style="padding:10px 8px;color:#555;font-size:13px;max-width:150px">
        {job.get("location","")}</td>
      <td style="padding:10px 8px;white-space:nowrap">
        {_freshness_badge(freshness)}</td>
      <td style="padding:10px 8px;text-align:center;font-size:13px;color:#555">
        {yoe_str}</td>
      <td style="padding:10px 8px">{_visa_tag(job.get("no_sponsorship", False))}</td>
      <td style="padding:10px 8px;white-space:nowrap">
        <div class="row-actions" style="display:flex;align-items:center;gap:4px;flex-wrap:wrap">
          <a href="{url}" target="_blank"
             style="background:#0066cc;color:#fff;padding:5px 10px;border-radius:6px;
                    font-size:12px;font-weight:600;text-decoration:none">Apply →</a>
          <button style="{_BTN_STYLE}" data-status="applied"  onclick="markJob(this)">✓ Applied</button>
          <button style="{_BTN_STYLE}" data-status="referred" onclick="markJob(this)">↗ Referred</button>
          <button style="{_BTN_STYLE}" data-status="rejected" onclick="markJob(this)">✗ Pass</button>
        </div>
      </td>
    </tr>"""


def _table(jobs, show_family=False):
    rows = "".join(_job_row(j, show_family=show_family) for j in jobs)
    return f"""
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="background:#f8f9fa;font-size:12px;color:#888;text-transform:uppercase">
          <th style="padding:8px;text-align:left;font-weight:600">Title / Company</th>
          <th style="padding:8px;text-align:left;font-weight:600">Location</th>
          <th style="padding:8px;text-align:left;font-weight:600">Posted</th>
          <th style="padding:8px;text-align:center;font-weight:600">Min YOE</th>
          <th style="padding:8px;text-align:left;font-weight:600">Visa</th>
          <th style="padding:8px;font-weight:600">Actions</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""


def _section(title, subtitle, jobs, accent="#0066cc", show_family=False):
    return f"""
  <div style="background:#fff;border-radius:10px;padding:20px 24px;margin-bottom:20px;
              box-shadow:0 1px 4px rgba(0,0,0,.08)">
    <h2 style="margin:0 0 4px;font-size:16px;font-weight:700;color:#1a1a1a;
               padding-bottom:8px;border-bottom:2px solid {accent}">
      {title}
      <span style="color:#999;font-weight:400;font-size:14px">({len(jobs)})</span>
    </h2>
    {f'<p style="margin:4px 0 10px;font-size:12px;color:#999">{subtitle}</p>' if subtitle else '<div style="margin-bottom:10px"></div>'}
    {_table(jobs, show_family=show_family)}
  </div>"""


def _sort(jobs):
    return sorted(jobs, key=lambda j: (j.get("freshness_tier", 99), j.get("company", "")))


def generate(new_jobs, run_time=None, window="2w"):
    """Write report.html. Returns the absolute path."""
    if run_time is None:
        run_time = datetime.now(tz=timezone.utc)

    ts    = run_time.strftime("%B %d, %Y at %I:%M %p UTC")
    total = len(new_jobs)

    hot  = _sort([j for j in new_jobs if j.get("freshness_tier", 99) <= 1])
    rest = [j for j in new_jobs if j.get("freshness_tier", 99) > 1]

    sections = ""
    if hot:
        sections += _section(
            "🔥 Posted in the Last 24 Hours",
            "Act on these first — newest postings move fastest.",
            hot, accent="#e63946", show_family=True,
        )
    for family in FAMILY_ORDER:
        fam_jobs = _sort([j for j in rest if j.get("role_family") == family])
        if fam_jobs:
            sections += _section(family, "", fam_jobs, accent="#0066cc")

    if not sections:
        sections = '<p style="color:#888;text-align:center;padding:40px">No new jobs this run.</p>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Job Watch — {ts}</title>
  <style>
    body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
            background:#f5f5f5;margin:0;padding:0; }}
    .container {{ max-width:1020px;margin:0 auto;padding:24px 16px; }}
    button:hover {{ background:#d0d0d0 !important; }}
  </style>
  {_JS}
</head>
<body>
<div class="container">
  <div style="background:#fff;border-radius:10px;padding:20px 24px;margin-bottom:24px;
              box-shadow:0 1px 4px rgba(0,0,0,.08)">
    <h1 style="margin:0 0 4px;font-size:22px;color:#1a1a1a">Job Watch</h1>
    <p style="margin:0;color:#666;font-size:14px">
      {ts} &nbsp;·&nbsp; window: {window} &nbsp;·&nbsp;
      <strong style="color:#0066cc">{total} new job{'s' if total != 1 else ''}</strong>
      &nbsp;·&nbsp;
      <span style="color:#e63946;font-weight:600">{len(hot)} in last 24h</span>
    </p>
    <p style="margin:8px 0 0;font-size:13px;color:#999">
      Click <strong>Apply →</strong> to open the posting, then mark your status
      with the buttons. Your tracker updates instantly — no CSV editing needed.
      &nbsp;·&nbsp;
      <a href="/tracker" style="color:#0066cc;font-weight:600;text-decoration:none">
        View Tracker →</a>
    </p>
  </div>

  {sections}

  <p style="text-align:center;color:#ccc;font-size:12px;margin-top:32px">
    Job Watch · {ts}
  </p>
</div>
</body>
</html>"""

    path = os.path.abspath(REPORT_FILE)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


# ── Server management ─────────────────────────────────────────────────────────

def _server_running():
    try:
        urllib.request.urlopen(SERVER_URL, timeout=2)
        return True
    except Exception:
        return False


def _start_server():
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
    subprocess.Popen(
        [sys.executable, script],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(10):
        time.sleep(0.5)
        if _server_running():
            return
    print("  [warn] Server didn't start — opening file:// fallback")


def notify(new_count, report_path, reviewable=None):
    """Ensure server is running, fire notification, open browser."""
    if reviewable is None:
        reviewable = new_count

    if not _server_running():
        print("  [server] Starting local server...")
        _start_server()

    if new_count > 0:
        msg      = f"{new_count} new job{'s' if new_count != 1 else ''} discovered!"
        subtitle = "Your report is ready — click to review."
    elif reviewable > 0:
        msg      = f"{reviewable} job{'s' if reviewable != 1 else ''} waiting for review."
        subtitle = "Opening your report now."
    else:
        msg      = "No new jobs this run."
        subtitle = "Nothing new to review."

    script = (
        f'display notification "{subtitle}" '
        f'with title "Job Watch — {msg}" '
        f'sound name "Purr"'
    )
    try:
        subprocess.run(["osascript", "-e", script], check=False)
    except Exception:
        pass

    if reviewable > 0:
        webbrowser.open(SERVER_URL)
