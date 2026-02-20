"""
Job Feed — Personal job aggregator web app.

Run:
    python app.py

Then visit http://localhost:5000
"""

import json
import os
import sqlite3
import threading
import time
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for

from db.database import get_connection, init_db
from scrapers.runner import run as run_scrapers

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

# ── Background Scraper ────────────────────────────────────────────────────────

SCRAPE_INTERVAL = int(os.environ.get("SCRAPE_INTERVAL_HOURS", 12)) * 3600
DEFAULT_TERMS = os.environ.get(
    "SEARCH_TERMS",
    "data analyst,bi engineer,business intelligence,analytics engineer,power bi,data engineer",
).split(",")


def background_scraper():
    """Runs in a daemon thread, scrapes on interval."""
    while True:
        time.sleep(SCRAPE_INTERVAL)
        try:
            run_scrapers(search_terms=DEFAULT_TERMS)
        except Exception as e:
            print(f"[bg-scraper] Error: {e}")


# Start background thread in production
if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("ENABLE_BG_SCRAPE"):
    t = threading.Thread(target=background_scraper, daemon=True)
    t.start()


# ── Feed Page (Home) ──────────────────────────────────────────────────────────


@app.route("/")
def feed():
    """Main job feed with filters."""
    conn = get_connection()

    # Get filter params
    source = request.args.get("source", "")
    search = request.args.get("search", "").strip()
    days = request.args.get("days", "")
    page = int(request.args.get("page", 1))
    per_page = 30

    # Build query
    where_clauses = []
    params = []

    if source:
        where_clauses.append("j.source_platform = ?")
        params.append(source)

    if search:
        where_clauses.append(
            "(j.title LIKE ? OR j.company LIKE ? OR j.tags LIKE ?)"
        )
        like = f"%{search}%"
        params.extend([like, like, like])

    if days:
        where_clauses.append("j.scraped_at >= datetime('now', ?)")
        params.append(f"-{days} days")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    count_row = conn.execute(
        f"SELECT COUNT(*) as cnt FROM job_posts j WHERE {where_sql}", params
    ).fetchone()
    total = count_row["cnt"]

    # Get paginated jobs with saved status
    offset = (page - 1) * per_page
    jobs = conn.execute(
        f"""
        SELECT j.*,
               CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END as is_saved,
               s.list_name as saved_list
        FROM job_posts j
        LEFT JOIN saved_jobs s ON j.id = s.job_id
        WHERE {where_sql}
        ORDER BY j.scraped_at DESC
        LIMIT ? OFFSET ?
        """,
        params + [per_page, offset],
    ).fetchall()

    # Get available sources for filter dropdown
    sources = conn.execute(
        "SELECT DISTINCT source_platform FROM job_posts ORDER BY source_platform"
    ).fetchall()

    # Get user lists
    lists = conn.execute("SELECT * FROM lists ORDER BY name").fetchall()

    total_pages = max(1, (total + per_page - 1) // per_page)

    conn.close()

    return render_template(
        "feed.html",
        jobs=jobs,
        sources=[r["source_platform"] for r in sources],
        lists=lists,
        current_source=source,
        current_search=search,
        current_days=days,
        page=page,
        total_pages=total_pages,
        total_jobs=total,
    )


# ── Saved Jobs Page ───────────────────────────────────────────────────────────


@app.route("/saved")
@app.route("/saved/<list_name>")
def saved(list_name: str = ""):
    conn = get_connection()

    lists = conn.execute("SELECT * FROM lists ORDER BY name").fetchall()

    where_sql = "1=1"
    params: list = []
    if list_name:
        where_sql = "s.list_name = ?"
        params = [list_name]

    jobs = conn.execute(
        f"""
        SELECT j.*, s.list_name, s.saved_at, s.id as saved_id
        FROM saved_jobs s
        JOIN job_posts j ON j.id = s.job_id
        WHERE {where_sql}
        ORDER BY s.saved_at DESC
        """,
        params,
    ).fetchall()

    # Count per list
    list_counts = {}
    for row in conn.execute(
        "SELECT list_name, COUNT(*) as cnt FROM saved_jobs GROUP BY list_name"
    ).fetchall():
        list_counts[row["list_name"]] = row["cnt"]

    conn.close()

    return render_template(
        "saved.html",
        jobs=jobs,
        lists=lists,
        list_counts=list_counts,
        current_list=list_name,
    )


# ── API: Save/Unsave Jobs ────────────────────────────────────────────────────


@app.route("/api/save", methods=["POST"])
def api_save_job():
    data = request.get_json()
    job_id = data.get("job_id")
    list_name = data.get("list_name", "Saved")

    if not job_id:
        return jsonify({"error": "job_id required"}), 400

    conn = get_connection()
    try:
        # Ensure list exists
        conn.execute("INSERT OR IGNORE INTO lists (name) VALUES (?)", (list_name,))
        conn.execute(
            "INSERT OR IGNORE INTO saved_jobs (job_id, list_name) VALUES (?, ?)",
            (job_id, list_name),
        )
        conn.commit()
        return jsonify({"status": "saved", "job_id": job_id, "list": list_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/unsave", methods=["POST"])
def api_unsave_job():
    data = request.get_json()
    job_id = data.get("job_id")
    list_name = data.get("list_name", "")

    conn = get_connection()
    if list_name:
        conn.execute(
            "DELETE FROM saved_jobs WHERE job_id = ? AND list_name = ?",
            (job_id, list_name),
        )
    else:
        conn.execute("DELETE FROM saved_jobs WHERE job_id = ?", (job_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "unsaved", "job_id": job_id})


# ── API: Manage Lists ────────────────────────────────────────────────────────


@app.route("/api/lists", methods=["POST"])
def api_create_list():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400

    conn = get_connection()
    try:
        conn.execute("INSERT INTO lists (name) VALUES (?)", (name,))
        conn.commit()
        return jsonify({"status": "created", "name": name})
    except sqlite3.IntegrityError:
        return jsonify({"error": "List already exists"}), 409
    finally:
        conn.close()


@app.route("/api/lists/<name>", methods=["DELETE"])
def api_delete_list(name: str):
    conn = get_connection()
    conn.execute("DELETE FROM saved_jobs WHERE list_name = ?", (name,))
    conn.execute("DELETE FROM lists WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted", "name": name})


# ── API: Trigger Scrape ───────────────────────────────────────────────────────


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    """Trigger a scrape in background thread."""
    data = request.get_json() or {}
    terms = data.get("terms")
    sources = data.get("sources")

    def _run():
        run_scrapers(search_terms=terms, sources=sources)

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return jsonify({"status": "scraping started", "terms": terms, "sources": sources})


# ── API: Stats ────────────────────────────────────────────────────────────────


@app.route("/api/stats")
def api_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) as cnt FROM job_posts").fetchone()["cnt"]
    by_source = conn.execute(
        "SELECT source_platform, COUNT(*) as cnt FROM job_posts GROUP BY source_platform"
    ).fetchall()
    saved_count = conn.execute("SELECT COUNT(*) as cnt FROM saved_jobs").fetchone()["cnt"]
    conn.close()

    return jsonify(
        {
            "total_jobs": total,
            "saved_jobs": saved_count,
            "by_source": {r["source_platform"]: r["cnt"] for r in by_source},
        }
    )


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n  \u{1f680} Job Feed running at http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
