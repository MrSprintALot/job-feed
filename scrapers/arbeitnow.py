"""Scraper for Arbeitnow.com free API."""

import json
import logging
import urllib.request

from scrapers.base import BaseScraper, JobPost

logger = logging.getLogger(__name__)

API_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowScraper(BaseScraper):
    name = "arbeitnow"

    def fetch_jobs(self, search_terms: list[str] | None = None) -> list[JobPost]:
        jobs: list[JobPost] = []
        page = 1
        max_pages = 3  # Limit to avoid hammering the API

        while page <= max_pages:
            url = f"{API_URL}?page={page}"
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "JobFeedApp/1.0"},
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode())
            except Exception as e:
                logger.error(f"Arbeitnow fetch page {page} failed: {e}")
                break

            items = data.get("data", [])
            if not items:
                break

            for item in items:
                title = item.get("title", "").strip()
                company = item.get("company_name", "").strip()
                job_url = item.get("url", "")
                if not job_url or not title:
                    continue

                tags_list = item.get("tags", [])
                tags_str = ", ".join(tags_list) if isinstance(tags_list, list) else str(tags_list)

                # Filter by search terms
                if search_terms:
                    searchable = f"{title} {tags_str} {company}".lower()
                    if not any(term.lower() in searchable for term in search_terms):
                        continue

                location = item.get("location", "Remote") or "Remote"
                remote = item.get("remote", False)
                if remote:
                    location = f"{location} (Remote)" if location != "Remote" else "Remote"

                posted = item.get("created_at", "")

                jobs.append(
                    JobPost(
                        title=title,
                        company=company,
                        url=job_url,
                        source_platform=self.name,
                        location=location,
                        salary="",
                        description=item.get("description", "")[:500],
                        tags=tags_str,
                        posted_at=str(posted),
                    )
                )

            # Check if there are more pages
            if not data.get("links", {}).get("next"):
                break
            page += 1

        logger.info(f"Arbeitnow: fetched {len(jobs)} jobs")
        return jobs
