"""SQLite database setup and helpers for the Job Feed app."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS job_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            role_category TEXT,
            source_platform TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            salary TEXT,
            description TEXT,
            tags TEXT,
            posted_at TEXT,
            scraped_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL REFERENCES job_posts(id) ON DELETE CASCADE,
            list_name TEXT NOT NULL DEFAULT 'Saved',
            saved_at TEXT DEFAULT (datetime('now')),
            UNIQUE(job_id, list_name)
        );

        CREATE TABLE IF NOT EXISTS lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Seed default list
        INSERT OR IGNORE INTO lists (name) VALUES ('Saved');

        CREATE INDEX IF NOT EXISTS idx_jobs_source ON job_posts(source_platform);
        CREATE INDEX IF NOT EXISTS idx_jobs_role ON job_posts(role_category);
        CREATE INDEX IF NOT EXISTS idx_jobs_posted ON job_posts(posted_at DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_url ON job_posts(url);
        CREATE INDEX IF NOT EXISTS idx_saved_list ON saved_jobs(list_name);
        """
    )
    conn.commit()
    conn.close()
