"""Base scraper interface for all job source scrapers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobPost:
    title: str
    company: str
    url: str
    source_platform: str
    location: str = "Remote"
    role_category: str = ""
    salary: str = ""
    description: str = ""
    tags: str = ""
    posted_at: str = ""


class BaseScraper(ABC):
    """All scrapers must implement the fetch_jobs method."""

    name: str = "base"

    @abstractmethod
    def fetch_jobs(self, search_terms: list[str] | None = None) -> list[JobPost]:
        """Fetch jobs from the source. Returns list of JobPost dataclasses."""
        ...
