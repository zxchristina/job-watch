# emailer.py — sends the Job Watch digest to your Gmail
#
# Uses the same HTML content as report.html so the email looks identical
# to what you see in the browser. Requires email_config.py.

import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from email_config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, SEND_TO
    _configured = True
except ImportError:
    _configured = False


def send(new_jobs, run_time=None, window="2w"):
    """
    Send the HTML digest email. Silently skips if email_config.py is missing
    or if there are no new jobs.
    """
    if not _configured:
        print("  [email] Skipping — email_config.py not found.")
        return
    if not new_jobs:
        print("  [email] Skipping — no new jobs to send.")
        return

    if run_time is None:
        run_time = datetime.now(tz=timezone.utc)

    html = _build_html(new_jobs, run_time, window)
    subject = _build_subject(new_jobs, run_time)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Job Watch <{GMAIL_ADDRESS}>"
    msg["To"]      = SEND_TO
    msg.attach(MIMEText(html, "html"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.ehlo()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, SEND_TO, msg.as_string())
        print(f"  [email] Digest sent → {SEND_TO}")
    except Exception as e:
        print(f"  [email] Failed to send: {e}")


def _build_subject(jobs, run_time):
    total = len(jobs)
    families = {}
    for j in jobs:
        f = j.get("role_family", "Other")
        families[f] = families.get(f, 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(families.items()))
    ts = run_time.strftime("%b %d %I:%M %p")
    return f"Job Watch — {total} new jobs ({ts} UTC): {summary}"


def _build_html(jobs, run_time, window):
    ts = run_time.strftime("%B %d, %Y at %I:%M %p UTC")
    total = len(jobs)

    family_order = [
        "Data Scientist", "Data Engineer", "Analytics Engineer", "ML / AI", "Analyst"
    ]

    def _sort(lst):
        return sorted(lst, key=lambda j: (j.get("freshness_tier", 99), j.get("company", "")))

    hot  = _sort([j for j in jobs if j.get("freshness_tier", 99) <= 1])
    rest = [j for j in jobs if j.get("freshness_tier", 99) > 1]

    sections = ""
    if hot:
        sections += _family_block("🔥 Posted in the Last 24 Hours — Act First", hot,
                                  accent="#e63946", show_family=True)
    for family in family_order:
        fam_jobs = _sort([j for j in rest if j.get("role_family") == family])
        if fam_jobs:
            sections += _family_block(family, fam_jobs)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
<div style="max-width:680px;margin:24px auto;padding:0 12px">

  <!-- Header -->
  <div style="background:#fff;border-radius:10px;padding:20px 24px;margin-bottom:20px;
              border:1px solid #e5e5e5">
    <h1 style="margin:0 0 4px;font-size:20px;color:#1a1a1a">Job Watch</h1>
    <p style="margin:0;color:#666;font-size:14px">
      {ts} &nbsp;·&nbsp; window: {window} &nbsp;·&nbsp;
      <strong style="color:#0066cc">{total} new job{'s' if total != 1 else ''}</strong>
    </p>
    <p style="margin:8px 0 0;font-size:13px;color:#999">
      Click <strong>Apply →</strong> on any role. Update tracker.csv to
      <em>applied / referred / rejected</em> so it won't resurface.
    </p>
  </div>

  {sections}

  <p style="text-align:center;color:#ccc;font-size:12px;margin-top:24px">
    Job Watch · {ts}
  </p>
</div>
</body>
</html>"""


def _family_block(family, jobs, accent="#0066cc", show_family=False):
    rows = "".join(_job_row(j, show_family=show_family) for j in jobs)
    return f"""
  <div style="background:#fff;border-radius:10px;padding:16px 20px;
              margin-bottom:16px;border:1px solid #e5e5e5">
    <h2 style="margin:0 0 12px;font-size:15px;font-weight:700;color:#333;
               padding-bottom:8px;border-bottom:2px solid {accent}">
      {family}
      <span style="color:#999;font-weight:400;font-size:13px">({len(jobs)})</span>
    </h2>
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead>
        <tr style="color:#aaa;font-size:11px;text-transform:uppercase">
          <th style="text-align:left;padding:4px 6px">Title / Company</th>
          <th style="text-align:left;padding:4px 6px">Age</th>
          <th style="text-align:center;padding:4px 6px">YOE</th>
          <th style="text-align:left;padding:4px 6px">Visa</th>
          <th style="padding:4px 6px"></th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>"""


_BADGE_COLORS = {
    "< 1 hour":   ("#d4edda", "#155724"),
    "< 24 hours": ("#d4edda", "#155724"),
    "< 48 hours": ("#fff3cd", "#856404"),
    "< 72 hours": ("#fff3cd", "#856404"),
    "< 1 week":   ("#ffe5d0", "#7d3c00"),
    "< 2 weeks":  ("#e2e3e5", "#383d41"),
    "unknown":    ("#e2e3e5", "#383d41"),
}


def _job_row(job, show_family=False):
    freshness = job.get("freshness", "unknown")
    bg, fg = _BADGE_COLORS.get(freshness, ("#e2e3e5", "#383d41"))
    no_sp = job.get("no_sponsorship", False)
    visa_bg = "#f8d7da" if (no_sp == "yes" or no_sp is True) else "#d4edda"
    visa_fg = "#721c24" if (no_sp == "yes" or no_sp is True) else "#155724"
    visa_txt = "NO VISA" if (no_sp == "yes" or no_sp is True) else "visa ok"
    yoe = job.get("min_yoe")
    yoe_str = f"{yoe}+" if yoe is not None else "?"
    url = job.get("url", "#")
    family_tag = (f' <span style="background:#f0f0f0;color:#666;padding:1px 5px;'
                  f'border-radius:6px;font-size:10px">{job.get("role_family","")}</span>'
                  if show_family else "")

    return f"""
      <tr style="border-bottom:1px solid #f5f5f5">
        <td style="padding:8px 6px">
          <strong style="color:#1a1a1a">{job.get("title","")}</strong>{family_tag}<br>
          <span style="color:#666">{job.get("company","")}</span>
        </td>
        <td style="padding:8px 6px;white-space:nowrap">
          <span style="background:{bg};color:{fg};padding:2px 7px;border-radius:10px;
                       font-size:11px;font-weight:600">{freshness}</span>
        </td>
        <td style="padding:8px 6px;text-align:center;color:#555">{yoe_str}</td>
        <td style="padding:8px 6px">
          <span style="background:{visa_bg};color:{visa_fg};padding:2px 7px;
                       border-radius:10px;font-size:11px;font-weight:600">{visa_txt}</span>
        </td>
        <td style="padding:8px 6px">
          <a href="{url}" style="background:#0066cc;color:#fff;padding:4px 10px;
             border-radius:5px;font-size:12px;font-weight:600;text-decoration:none">
            Apply →</a>
        </td>
      </tr>"""
