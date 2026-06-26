#!/usr/bin/env python3
# server.py — persistent local server for Job Watch
#
# Runs on http://localhost:8765
# - Serves report.html with live status buttons
# - Handles /mark?key=...&status=... to update tracker.csv in real time
#
# Started automatically by runner.py if not already running.
# Also started at login by launchd (set up separately).

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

PORT = 8765

# Resolve paths relative to this file so launchd can start it from anywhere
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE  = os.path.join(BASE_DIR, "report.html")

# Make sure imports from this project work
sys.path.insert(0, BASE_DIR)
import tracker


class Handler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass   # suppress noisy access logs

    def _send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        # ── Serve the HTML report ─────────────────────────────────────────────
        if parsed.path in ("/", "/report"):
            if not os.path.exists(REPORT_FILE):
                body = b"<h2>No report yet.</h2><p>Run <code>python runner.py</code> first.</p>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)
                return
            with open(REPORT_FILE, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        # ── Mark a job status ─────────────────────────────────────────────────
        elif parsed.path == "/mark":
            params   = parse_qs(parsed.query)
            key      = params.get("key",    [""])[0]
            status   = params.get("status", [""])[0]
            valid    = {"applied", "referred", "rejected", "new"}

            if not key or status not in valid:
                self._send_json(400, {"ok": False, "error": "bad params"})
                return

            os.chdir(BASE_DIR)
            records = tracker.load()
            if key not in records:
                self._send_json(404, {"ok": False, "error": "key not found"})
                return

            records[key]["status"] = status
            tracker.save(records)
            self._send_json(200, {"ok": True, "key": key, "status": status})

        # ── Tracker view ──────────────────────────────────────────────────────
        elif parsed.path == "/tracker":
            body = _build_tracker_page().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()


_STATUS_STYLE = {
    "applied":  ("#d4edda", "#155724", "✓ Applied"),
    "referred": ("#fff3cd", "#856404", "↗ Referred"),
    "rejected": ("#f8d7da", "#721c24", "✗ Passed"),
    "new":      ("#e8f0fe", "#1a56db", "● New"),
}

_CHANGE_BTN = (
    "background:#f0f0f0;color:#333;border:none;padding:3px 8px;"
    "border-radius:5px;font-size:11px;cursor:pointer;margin:0 2px"
)

_TRACKER_JS = """
<script>
function changeStatus(key, status) {
  fetch(`/mark?key=${encodeURIComponent(key)}&status=${encodeURIComponent(status)}`)
    .then(r => r.json())
    .then(d => { if (d.ok) location.reload(); });
}
</script>
"""

def _build_tracker_page():
    os.chdir(BASE_DIR)
    records = tracker.load()

    counts = {"applied": 0, "referred": 0, "rejected": 0, "new": 0}
    for r in records.values():
        s = r.get("status", "new")
        counts[s] = counts.get(s, 0) + 1

    nav = (
        '<a href="/" style="color:#0066cc;text-decoration:none;font-weight:600">'
        '← Back to Jobs</a>'
    )

    # Summary pills
    pills = ""
    for status, label in [("applied","Applied"), ("referred","Referred"),
                           ("rejected","Passed"), ("new","New")]:
        bg, fg, _ = _STATUS_STYLE[status]
        pills += (
            f'<span style="background:{bg};color:{fg};padding:4px 12px;'
            f'border-radius:12px;font-size:13px;font-weight:600;margin-right:8px">'
            f'{label}: {counts.get(status,0)}</span>'
        )

    # Build sections in priority order
    section_order = [
        ("applied",  "✓ Applied"),
        ("referred", "↗ Referred"),
        ("new",      "● Still to Review"),
        ("rejected", "✗ Passed"),
    ]

    sections_html = ""
    for status, heading in section_order:
        jobs = sorted(
            [r for r in records.values() if r.get("status") == status],
            key=lambda r: r.get("posted_at", ""), reverse=True
        )
        if not jobs:
            continue

        bg, fg, _ = _STATUS_STYLE[status]
        rows = ""
        for j in jobs:
            other_statuses = [s for s in ["applied","referred","rejected","new"]
                              if s != status]
            change_btns = "".join(
                f'<button style="{_CHANGE_BTN}" '
                f'onclick="changeStatus(\'{j["key"]}\',\'{s}\')">'
                f'{_STATUS_STYLE[s][2]}</button>'
                for s in other_statuses
            )
            rows += f"""
            <tr style="border-bottom:1px solid #f0f0f0">
              <td style="padding:9px 8px;max-width:260px">
                <a href="{j.get('url','#')}" target="_blank"
                   style="color:#1a1a1a;font-weight:600;font-size:13px;text-decoration:none">
                  {j.get('title','')}</a><br>
                <span style="color:#666;font-size:12px">{j.get('company','')}</span>
              </td>
              <td style="padding:9px 8px;font-size:12px;color:#555">{j.get('role_family','')}</td>
              <td style="padding:9px 8px;font-size:12px;color:#777">{j.get('location','')}</td>
              <td style="padding:9px 8px;font-size:12px;color:#999">{j.get('posted_at','')[:10]}</td>
              <td style="padding:9px 8px;white-space:nowrap">{change_btns}</td>
            </tr>"""

        sections_html += f"""
        <div style="background:#fff;border-radius:10px;padding:18px 22px;
                    margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.07)">
          <h2 style="margin:0 0 12px;font-size:15px;font-weight:700;
                     padding-bottom:7px;border-bottom:2px solid {bg};color:#1a1a1a">
            <span style="background:{bg};color:{fg};padding:2px 10px;
                         border-radius:8px;margin-right:8px">{heading}</span>
            <span style="color:#999;font-weight:400;font-size:13px">({len(jobs)})</span>
          </h2>
          <table style="width:100%;border-collapse:collapse;font-size:13px">
            <thead>
              <tr style="font-size:11px;color:#aaa;text-transform:uppercase">
                <th style="padding:5px 8px;text-align:left">Title / Company</th>
                <th style="padding:5px 8px;text-align:left">Family</th>
                <th style="padding:5px 8px;text-align:left">Location</th>
                <th style="padding:5px 8px;text-align:left">Posted</th>
                <th style="padding:5px 8px">Change Status</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Job Watch — Tracker</title>
  <style>
    body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
            background:#f5f5f5;margin:0;padding:0; }}
    .container {{ max-width:980px;margin:0 auto;padding:24px 16px; }}
    button:hover {{ background:#d8d8d8 !important; }}
  </style>
  {_TRACKER_JS}
</head>
<body>
<div class="container">
  <div style="background:#fff;border-radius:10px;padding:18px 22px;margin-bottom:20px;
              box-shadow:0 1px 4px rgba(0,0,0,.07)">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <h1 style="margin:0 0 4px;font-size:20px;color:#1a1a1a">Job Watch — Tracker</h1>
        <p style="margin:0;color:#999;font-size:13px">
          All {len(records)} jobs ever seen. Updates live as you click.</p>
      </div>
      <div>{nav}</div>
    </div>
    <div style="margin-top:12px">{pills}</div>
  </div>
  {sections_html}
</div>
</body>
</html>"""


def run():
    os.chdir(BASE_DIR)
    httpd = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Job Watch server → http://localhost:{PORT}  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    run()
