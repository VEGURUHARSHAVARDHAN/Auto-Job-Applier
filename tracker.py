"""
agents/tracker.py
Tracks all job applications in a local SQLite database.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict

DB_PATH = "data/tracker.db"


def init_db():
    """Create the database and tables if they don't exist."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            company      TEXT NOT NULL,
            location     TEXT,
            source       TEXT,
            link         TEXT,
            status       TEXT DEFAULT 'applied',
            match_score  INTEGER DEFAULT 0,
            applied_date TEXT,
            followup_date TEXT,
            notes        TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_application(job: Dict, status: str = "applied"):
    """Save or update a job application in the database."""
    conn = sqlite3.connect(DB_PATH)
    
    # Check if already exists
    existing = conn.execute(
        "SELECT id FROM applications WHERE title=? AND company=?",
        (job.get("title", ""), job.get("company", ""))
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE applications SET status=?, applied_date=? WHERE id=?",
            (status, datetime.now().strftime("%Y-%m-%d %H:%M"), existing[0])
        )
    else:
        conn.execute(
            """INSERT INTO applications
               (title, company, location, source, link, status, match_score, applied_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("source", ""),
                job.get("link", ""),
                status,
                job.get("match_score", 0),
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )
        )
    conn.commit()
    conn.close()


def get_all_applications() -> List[Dict]:
    """Return all tracked applications."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM applications ORDER BY applied_date DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_applications_by_status(status: str) -> List[Dict]:
    """Return applications with a specific status."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM applications WHERE status=? ORDER BY applied_date DESC",
        (status,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_status(app_id: int, status: str, notes: str = ""):
    """Update the status of an application."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE applications SET status=?, notes=? WHERE id=?",
        (status, notes, app_id)
    )
    conn.commit()
    conn.close()


def print_summary():
    """Print a summary table of all applications."""
    apps = get_all_applications()
    if not apps:
        print("No applications tracked yet.")
        return

    print(f"\n{'─'*80}")
    print(f"{'#':<4} {'Title':<35} {'Company':<25} {'Status':<12} {'Score':<6}")
    print(f"{'─'*80}")
    for i, app in enumerate(apps, 1):
        print(f"{i:<4} {app['title'][:34]:<35} {app['company'][:24]:<25} "
              f"{app['status']:<12} {app.get('match_score', '-'):<6}")
    print(f"{'─'*80}")
    
    statuses = {}
    for app in apps:
        statuses[app["status"]] = statuses.get(app["status"], 0) + 1
    print("  " + " | ".join(f"{k}: {v}" for k, v in statuses.items()))
    print()
