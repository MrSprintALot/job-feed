"""Scraper for RemoteOK.com free API."""

import json
import logging
import urllib.request
from datetime import datetime

from scrapers.base import BaseScraper, JobPost

logger = logging.getLogger(__name__)

API_URL = "https://remoteok.com/api"


class RemoteOKScraper(BaseScraper):
    name = "remoteok"

    def fetch_jobs(self, search_terms: list[str] | None = None) -> list[JobPost]:
        jobs: list[JobPost] = []
        try:
            req = urllib.request.Request(
                API_URL,
                headers={"User-Agent": "JobFeedApp/1.0"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"RemoteOK fetch failed: {e}")
            return jobs

        # First item is a legal notice, skip it
        listings = data[1:] if len(data) > 1 else data

        for item in listings:
            title = item.get("position", "").strip()
            company = item.get("company", "").strip()
            url = item.get("url", "")
            if not url and item.get("slug"):
                url = f"https://remoteok.com/remote-jobs/{item['slug']}"
            if not url or not title:
                continue

            tags_list = item.get("tags", [])
            tags_str = ", ".join(tags_list) if isinstance(tags_list, list) else str(tags_list)

            # Filter by search terms if provided
            if search_terms:
                searchable = f"{title} {tags_str} {company}".lower()
                if not any(term.lower() in searchable for term in search_terms):
                    continue

            posted = item.get("date", "")
            if posted:
                try:
                    dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                    posted = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    pass

            salary_min = item.get("salary_min", "")
            salary_max = item.get("salary_max", "")
            salary = ""
            if salary_min and salary_max:
                salary = f"${int(salary_min):,} – ${int(salary_max):,}"
            elif salary_min:
                salary = f"${int(salary_min):,}+"

            location = item.get("location", "Remote") or "Remote"

            jobs.append(
                JobPost(
                    title=title,
                    company=company,
                    url=url,
                    source_platform=self.name,
                    location=location,
                    salary=salary,
                    description=item.get("description", "")[:500],
                    tags=tags_str,
                    posted_at=posted,
                )
            )

        logger.info(f"RemoteOK: fetched {len(jobs)} jobs")
        return jobs
