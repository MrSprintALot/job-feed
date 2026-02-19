"""Scraper for Jobicy.com free API."""

import json
import logging
import urllib.request

from scrapers.base import BaseScraper, JobPost

logger = logging.getLogger(__name__)

API_URL = "https://jobicy.com/api/v2/remote-jobs"


class JobicyScraper(BaseScraper):
    name = "jobicy"

    def fetch_jobs(
        self,
        search_terms: list[str] | None = None,
        geo: str = "",
        industry: str = "",
        count: int = 50,
    ) -> list[JobPost]:
        jobs: list[JobPost] = []

        params = [f"count={count}"]
        if geo:
            params.append(f"geo={geo}")
        if industry:
            params.append(f"industry={industry}")
        if search_terms:
            params.append(f"tag={'+'.join(search_terms)}")

        url = API_URL + "?" + "&".join(params)

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "JobFeedApp/1.0"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"Jobicy fetch failed: {e}")
            return jobs

        for item in data.get("jobs", []):
            title = item.get("jobTitle", "").strip()
            company = item.get("companyName", "").strip()
            job_url = item.get("url", "")
            if not job_url or not title:
                continue

            salary_min = item.get("annualSalaryMin", "")
            salary_max = item.get("annualSalaryMax", "")
            salary_currency = item.get("salaryCurrency", "USD")
            salary = ""
            if salary_min and salary_max:
                salary = f"{salary_currency} {salary_min} – {salary_max}"
            elif salary_min:
                salary = f"{salary_currency} {salary_min}+"

            location = item.get("jobGeo", "Remote") or "Remote"
            industry_label = item.get("jobIndustry", "")
            if isinstance(industry_label, list):
                industry_label = ", ".join(industry_label)

            posted = item.get("pubDate", "")

            jobs.append(
                JobPost(
                    title=title,
                    company=company,
                    url=job_url,
                    source_platform=self.name,
                    location=location,
                    role_category=industry_label,
                    salary=salary,
                    description=item.get("jobDescription", "")[:500],
                    tags=item.get("jobType", ""),
                    posted_at=posted,
                )
            )

        logger.info(f"Jobicy: fetched {len(jobs)} jobs")
        return jobs
