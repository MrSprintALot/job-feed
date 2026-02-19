"""Scraper for Remotive.com free API."""

import json
import logging
import urllib.request
from datetime import datetime

from scrapers.base import BaseScraper, JobPost

logger = logging.getLogger(__name__)

API_URL = "https://remotive.com/api/remote-jobs"

# Map Remotive categories to our role categories
CATEGORY_MAP = {
    "data": "data",
    "software-dev": "software-dev",
    "devops": "devops",
    "product": "product",
    "marketing": "marketing",
    "business": "business",
    "all": "",
}


class RemotiveScraper(BaseScraper):
    name = "remotive"

    def fetch_jobs(
        self,
        search_terms: list[str] | None = None,
        category: str = "",
    ) -> list[JobPost]:
        jobs: list[JobPost] = []

        url = API_URL
        params = []
        if category:
            params.append(f"category={category}")
        if search_terms:
            params.append(f"search={'+'.join(search_terms)}")
        if params:
            url += "?" + "&".join(params)

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "JobFeedApp/1.0"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"Remotive fetch failed: {e}")
            return jobs

        for item in data.get("jobs", []):
            title = item.get("title", "").strip()
            company = item.get("company_name", "").strip()
            job_url = item.get("url", "")
            if not job_url or not title:
                continue

            tags_list = item.get("tags", [])
            tags_str = ", ".join(tags_list) if isinstance(tags_list, list) else str(tags_list)

            posted = item.get("publication_date", "")
            if posted:
                try:
                    dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                    posted = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    pass

            salary = item.get("salary", "") or ""
            location = item.get("candidate_required_location", "Remote") or "Remote"
            category_label = item.get("category", "")

            jobs.append(
                JobPost(
                    title=title,
                    company=company,
                    url=job_url,
                    source_platform=self.name,
                    location=location,
                    role_category=category_label,
                    salary=salary,
                    description=item.get("description", "")[:500],
                    tags=tags_str,
                    posted_at=posted,
                )
            )

        logger.info(f"Remotive: fetched {len(jobs)} jobs")
        return jobs
