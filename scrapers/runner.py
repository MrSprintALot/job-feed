"""
Scraper runner: orchestrates all scrapers, deduplicates, and inserts into SQLite.

Usage:
    python -m scrapers.runner                          # Fetch all, no filter
    python -m scrapers.runner --terms "data analyst" "bi engineer" "analytics"
    python -m scrapers.runner --sources remoteok remotive
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_connection, init_db
from scrapers.arbeitnow import ArbeitnowScraper
from scrapers.base import JobPost
from scrapers.jobicy import JobicyScraper
from scrapers.remoteok import RemoteOKScraper
from scrapers.remotive import RemotiveScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

ALL_SCRAPERS = {
    "remoteok": RemoteOKScraper,
    "remotive": RemotiveScraper,
    "jobicy": JobicyScraper,
    "arbeitnow": ArbeitnowScraper,
}


def insert_jobs(jobs: list[JobPost]) -> tuple[int, int]:
    """Insert jobs into DB, skipping duplicates. Returns (inserted, skipped)."""
    conn = get_connection()
    inserted = 0
    skipped = 0

    for job in jobs:
        try:
            conn.execute(
                """
                INSERT INTO job_posts
                    (title, company, location, role_category, source_platform,
                     url, salary, description, tags, posted_at, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.title,
                    job.company,
                    job.location,
                    job.role_category,
                    job.source_platform,
                    job.url,
                    job.salary,
                    job.description,
                    job.tags,
                    job.posted_at,
                    datetime.now().isoformat(),
                ),
            )
            inserted += 1
        except Exception:
            skipped += 1  # URL already exists (duplicate)

    conn.commit()
    conn.close()
    return inserted, skipped


def run(
    search_terms: list[str] | None = None,
    sources: list[str] | None = None,
) -> dict:
    """Run scrapers and return stats."""
    init_db()
    stats: dict[str, dict] = {}

    scrapers_to_run = {
        name: cls
        for name, cls in ALL_SCRAPERS.items()
        if sources is None or name in sources
    }

    all_jobs: list[JobPost] = []

    for name, scraper_cls in scrapers_to_run.items():
        logger.info(f"Running {name} scraper...")
        scraper = scraper_cls()
        try:
            jobs = scraper.fetch_jobs(search_terms=search_terms)
            all_jobs.extend(jobs)
            stats[name] = {"fetched": len(jobs), "status": "ok"}
        except Exception as e:
            logger.error(f"{name} failed: {e}")
            stats[name] = {"fetched": 0, "status": f"error: {e}"}

    inserted, skipped = insert_jobs(all_jobs)
    stats["_total"] = {
        "fetched": len(all_jobs),
        "inserted": inserted,
        "skipped_duplicates": skipped,
    }

    logger.info(
        f"Done: {len(all_jobs)} fetched, {inserted} new, {skipped} duplicates"
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Run job scrapers")
    parser.add_argument(
        "--terms",
        nargs="+",
        help="Search terms to filter jobs (e.g., 'data analyst' 'bi engineer')",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=list(ALL_SCRAPERS.keys()),
        help="Which sources to scrape",
    )
    args = parser.parse_args()

    stats = run(search_terms=args.terms, sources=args.sources)

    print("\n--- Scrape Results ---")
    for source, info in stats.items():
        print(f"  {source}: {info}")


if __name__ == "__main__":
    main()
