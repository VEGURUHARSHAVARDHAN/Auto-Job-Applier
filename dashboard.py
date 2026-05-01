"""
dashboard.py — Web dashboard to view and manage job applications.
Run: python dashboard.py
Then open: http://localhost:8080
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import json
import os
import urllib.parse

DB_PATH = "data/tracker.db"


def get_stats():
    if not os.path.exists(DB_PATH):
        return {"total": 0, "applied": 0, "interview": 0, "rejected": 0, "followup": 0}
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT status, COUNT(*) FROM applications GROUP BY status").fetchall()
    conn.close()
    stats = {"total": 0, "applied": 0, "interview": 0, "rejected": 0, "followup": 0}
    for status, count in rows:
        stats["total"] += count
        key = status.replace("_sent", "").replace("followup", "followup")
        if key in stats:
            stats[key] += count
    return stats


def get_applications():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM applications ORDER BY applied_date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Job Applier Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

  :root {
    --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
    --accent: #7c6ff7; --accent2: #4ecdc4; --success: #56cf89;
    --warn: #f5a623; --danger: #ff6b6b; --text: #e8eaf0; --muted: #8a8fa8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

  header { border-bottom: 1px solid var(--border); padding: 20px 32px; display: flex; align-items: center; gap: 12px; }
  .logo { font-size: 22px; font-weight: 600; letter-spacing: -0.5px; }
  .logo span { color: var(--accent); }
  .subtitle { color: var(--muted); font-size: 13px; margin-left: auto; }

  .main { max-width: 1200px; margin: 0 auto; padding: 32px 24px; }

  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 32px; }
  .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
  .stat-number { font-size: 36px; font-weight: 600; font-family: 'DM Mono', monospace; }
  .stat-label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
  .stat-card.total .stat-number  { color: var(--accent); }
  .stat-card.applied .stat-number { color: var(--accent2); }
  .stat-card.interview .stat-number { color: var(--success); }
  .stat-card.followup .stat-number { color: var(--warn); }
  .stat-card.rejected .stat-number { color: var(--danger); }

  .section-title { font-size: 14px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px; }

  .filter-bar { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
  .filter-btn { padding: 6px 16px; border-radius: 20px; border: 1px solid var(--border); background: transparent; color: var(--muted); font-size: 13px; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.15s; }
  .filter-btn:hover, .filter-btn.active { background: var(--accent); border-color: var(--accent); color: white; }

  table { width: 100%; border-collapse: collapse; }
  thead th { text-align: left; padding: 10px 14px; font-size: 11px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
  tbody tr { border-bottom: 1px solid var(--border); transition: background 0.1s; }
  tbody tr:hover { background: var(--surface); }
  tbody td { padding: 14px; font-size: 14px; }

  .badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }
  .badge.applied   { background: rgba(78,205,196,0.15); color: var(--accent2); }
  .badge.pending   { background: rgba(245,166,35,0.15); color: var(--warn); }
  .badge.failed    { background: rgba(255,107,107,0.15); color: var(--danger); }
  .badge.interview { background: rgba(86,207,137,0.15); color: var(--success); }
  .badge.followup_sent { background: rgba(124,111,247,0.15); color: var(--accent); }
  .badge.rejected  { background: rgba(255,107,107,0.15); color: var(--danger); }

  .source-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; margin-right: 6px; }
  .source-naukri  { background: #ff6b35; }
  .source-indeed  { background: #2557a7; }
  .source-linkedin { background: #0a66c2; }

  .score-bar { display: flex; align-items: center; gap: 8px; }
  .bar { height: 4px; width: 60px; background: var(--border); border-radius: 2px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 2px; }
  .score-text { font-family: 'DM Mono', monospace; font-size: 12px; color: var(--muted); }

  .link-btn { color: var(--accent); text-decoration: none; font-size: 12px; opacity: 0.7; }
  .link-btn:hover { opacity: 1; }

  .empty { text-align: center; padding: 60px; color: var(--muted); }
  .empty .icon { font-size: 48px; margin-bottom: 12px; }

  .refresh-btn { margin-left: auto; padding: 8px 16px; background: var(--accent); border: none; border-radius: 8px; color: white; font-size: 13px; cursor: pointer; font-family: 'DM Sans', sans-serif; }
</style>
</head>
<body>

<header>
  <div class="logo">🤖 Job<span>Agent</span></div>
  <div class="subtitle">Auto Job Applier Dashboard</div>
  <button class="refresh-btn" onclick="location.reload()">↻ Refresh</button>
</header>

<div class="main">
  <div class="stats-grid" id="stats"></div>

  <div class="section-title">Applications</div>
  <div class="filter-bar" id="filters"></div>

  <table>
    <thead>
      <tr>
        <th>#</th><th>Job Title</th><th>Company</th><th>Source</th>
        <th>Match</th><th>Status</th><th>Applied</th><th>Link</th>
      </tr>
    </thead>
    <tbody id="table-body"></tbody>
  </table>
  <div id="empty" class="empty" style="display:none">
    <div class="icon">📭</div>
    <div>No applications yet. Run main.py to start!</div>
  </div>
</div>

<script>
let allApps = [];
let activeFilter = 'all';

async function load() {
  const [stats, apps] = await Promise.all([
    fetch('/api/stats').then(r => r.json()),
    fetch('/api/apps').then(r => r.json())
  ]);
  allApps = apps;
  renderStats(stats);
  renderFilters(stats);
  renderTable(apps);
}

function renderStats(s) {
  const cards = [
    {key:'total',    label:'Total',      val: s.total},
    {key:'applied',  label:'Applied',    val: s.applied},
    {key:'interview',label:'Interview',  val: s.interview},
    {key:'followup', label:'Follow-up',  val: s.followup},
    {key:'rejected', label:'Rejected',   val: s.rejected},
  ];
  document.getElementById('stats').innerHTML = cards.map(c =>
    `<div class="stat-card ${c.key}">
      <div class="stat-number">${c.val}</div>
      <div class="stat-label">${c.label}</div>
    </div>`
  ).join('');
}

function renderFilters(stats) {
  const filters = ['all', 'applied', 'pending', 'interview', 'followup_sent', 'rejected'];
  document.getElementById('filters').innerHTML = filters.map(f =>
    `<button class="filter-btn ${f === activeFilter ? 'active' : ''}"
      onclick="filterBy('${f}')">${f === 'all' ? 'All' : f.replace('_', ' ')}</button>`
  ).join('');
}

function filterBy(status) {
  activeFilter = status;
  const filtered = status === 'all' ? allApps : allApps.filter(a => a.status === status);
  renderFilters({});
  renderTable(filtered);
}

function scoreColor(score) {
  if (score >= 80) return '#56cf89';
  if (score >= 60) return '#f5a623';
  return '#ff6b6b';
}

function renderTable(apps) {
  const tbody = document.getElementById('table-body');
  const empty = document.getElementById('empty');
  if (!apps.length) { tbody.innerHTML = ''; empty.style.display = ''; return; }
  empty.style.display = 'none';
  tbody.innerHTML = apps.map((a, i) => `
    <tr>
      <td style="color:var(--muted);font-family:'DM Mono',monospace;font-size:12px">${i+1}</td>
      <td style="font-weight:500">${a.title || '-'}</td>
      <td style="color:var(--muted)">${a.company || '-'}</td>
      <td>
        <span class="source-dot source-${a.source || 'other'}"></span>
        <span style="font-size:12px;color:var(--muted)">${a.source || '-'}</span>
      </td>
      <td>
        <div class="score-bar">
          <div class="bar"><div class="bar-fill" style="width:${a.match_score||0}%;background:${scoreColor(a.match_score||0)}"></div></div>
          <span class="score-text">${a.match_score || 0}</span>
        </div>
      </td>
      <td><span class="badge ${a.status || 'applied'}">${(a.status||'applied').replace('_',' ')}</span></td>
      <td style="font-size:12px;color:var(--muted)">${(a.applied_date||'').slice(0,10)}</td>
      <td>${a.link ? `<a href="${a.link}" class="link-btn" target="_blank">↗ Open</a>` : '-'}</td>
    </tr>
  `).join('');
}

load();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            self._respond(200, "text/html", HTML.encode())
        elif path == "/api/stats":
            self._respond(200, "application/json", json.dumps(get_stats()).encode())
        elif path == "/api/apps":
            self._respond(200, "application/json", json.dumps(get_applications()).encode())
        else:
            self._respond(404, "text/plain", b"Not found")

    def _respond(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Suppress access logs


if __name__ == "__main__":
    port = 8080
    print(f"🌐 Dashboard running at http://localhost:{port}")
    print("   Press Ctrl+C to stop")
    HTTPServer(("", port), Handler).serve_forever()
