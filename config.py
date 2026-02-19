"""
Configuration for the Job Feed app.

Edit these to customize what jobs you see.
"""

# ── Search Terms ──────────────────────────────────────────────
# These are used when running scrapers to filter relevant jobs.
# Add/remove terms to match the roles you're targeting.

SEARCH_TERMS = [
    "data analyst",
    "business intelligence",
    "bi engineer",
    "analytics engineer",
    "power bi",
    "data engineer",
    "analytics",
]

# ── Sources to Scrape ────────────────────────────────────────
# Comment out any you don't want.

ACTIVE_SOURCES = [
    "remoteok",
    "remotive",
    "jobicy",
    "arbeitnow",
]

# ── Scraping Schedule ────────────────────────────────────────
# If you set up a cron job, use this interval (in hours).
SCRAPE_INTERVAL_HOURS = 12

# ── Remotive Category ────────────────────────────────────────
# Remotive supports category filtering. Options:
# software-dev, data, devops, product, marketing, business, etc.
REMOTIVE_CATEGORY = "data"

# ── Jobicy Settings ──────────────────────────────────────────
# geo options: "usa", "europe", "latam", etc.
JOBICY_GEO = ""  # empty = all regions
JOBICY_INDUSTRY = ""  # empty = all industries
JOBICY_COUNT = 50
