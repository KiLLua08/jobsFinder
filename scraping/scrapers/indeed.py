"""
IndeedScraper — Scrapes job listings from Indeed's public job search.

This class inherits from BaseScraper and only needs to implement:
  1. get_search_url()  → builds the Indeed search URL
  2. parse_job_cards() → extracts job data from Indeed's HTML

Everything else (browser, retries, anti-detection, pagination)
is handled by the parent BaseScraper class.

NOTES ON INDEED'S STRUCTURE:
  - Search URL: https://www.indeed.com/jobs?q=<query>&start=<offset>
  - Each result page shows ~15 jobs
  - Job cards are <div> elements with the attribute data-testid="slider_item"
    or class="job_seen_beacon"
  - Individual job links are relative (e.g. /rc/clk?jk=abc123) and must
    be made absolute before navigating to them
  - Full job descriptions live at https://www.indeed.com/viewjob?jk=<jk>
"""

import logging
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from scraping.utils.anti_detection import get_random_user_agent, random_delay
from .base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.indeed.com"


class IndeedScraper(BaseScraper):
    """Scraper for Indeed's public job search page.

    NOTE: Indeed renders most of its content server-side, so the basic
    HTML is available without JavaScript execution. However, Indeed is
    aggressive about bot detection — we rely on the anti-detection
    headers and delays already built into BaseScraper.

    If Indeed blocks the headless browser, the scraper will find 0 cards
    on the page. In that case, try increasing the random delay ranges or
    rotating proxies.
    """

    # Indeed shows ~15 jobs per page
    JOBS_PER_PAGE = 15

    def get_search_url(self, query, page=1):
        """Build the Indeed job search URL.

        Indeed's public job search uses this URL pattern:
          https://www.indeed.com/jobs?q=<query>&start=<offset>

        The 'start' parameter controls pagination:
          Page 1 → start=0
          Page 2 → start=15
          Page 3 → start=30

        quote_plus() encodes the query for URLs:
          "Data Scientist" → "Data+Scientist"
        """
        encoded_query = quote_plus(query)
        offset = (page - 1) * self.JOBS_PER_PAGE
        return f"{BASE_URL}/jobs?q={encoded_query}&start={offset}"

    def parse_job_cards(self, page_source):
        """Extract job listings from Indeed's HTML.

        HOW THIS WORKS:
        1. BeautifulSoup parses the raw HTML into a tree structure
        2. We look for job cards — Indeed uses a few different layouts
           depending on A/B tests, so we try multiple selectors
        3. From each card, we extract title, company, location, and link
        4. We return a list of dicts

        DEFENSIVE PARSING:
        We use .find() which returns None if not found, and we check
        for None before calling .text — this prevents crashes if
        Indeed changes their HTML structure.
        """
        soup = BeautifulSoup(page_source, "html.parser")

        # Indeed uses a few different card containers; try both
        job_cards = soup.find_all("div", class_="job_seen_beacon")
        if not job_cards:
            # Fallback: newer Indeed layout uses data-testid
            job_cards = soup.find_all("div", attrs={"data-testid": "slider_item"})

        logger.debug(f"Found {len(job_cards)} raw job cards on page")
        jobs = []

        for card in job_cards:
            try:
                # ── Title ──────────────────────────────────────────
                # Indeed wraps the title in <h2> with data-testid="jobTitle"
                title_tag = card.find("h2", attrs={"data-testid": "jobTitle"})
                if title_tag:
                    # The actual text is in a <span> inside the <h2>
                    title_span = title_tag.find("span")
                    title = title_span.get_text(strip=True) if title_span else title_tag.get_text(strip=True)
                else:
                    # Fallback for older layout
                    title_tag = card.find("a", class_="jcs-JobTitle")
                    title = title_tag.get_text(strip=True) if title_tag else None

                # ── Company ────────────────────────────────────────
                company_tag = card.find("span", attrs={"data-testid": "company-name"})
                if not company_tag:
                    company_tag = card.find("span", class_="companyName")
                company = company_tag.get_text(strip=True) if company_tag else None

                # ── Location ───────────────────────────────────────
                location_tag = card.find("div", attrs={"data-testid": "text-location"})
                if not location_tag:
                    location_tag = card.find("div", class_="companyLocation")
                location = location_tag.get_text(strip=True) if location_tag else ""

                # ── Link ───────────────────────────────────────────
                # The job link is on the <h2>/<a> title element
                link_tag = card.find("a", attrs={"data-jk": True})
                if not link_tag:
                    link_tag = card.find("a", class_="jcs-JobTitle")

                if link_tag and link_tag.get("href"):
                    raw_href = link_tag["href"]
                    # Make the URL absolute if it's relative
                    link = raw_href if raw_href.startswith("http") else urljoin(BASE_URL, raw_href)
                    # Also pull out the job key (jk) for the viewjob URL
                    jk = link_tag.get("data-jk") or _extract_jk(link)
                    # The canonical, stable URL for a job is /viewjob?jk=<jk>
                    if jk:
                        link = f"{BASE_URL}/viewjob?jk={jk}"
                else:
                    link = None

                # Only add if we have the essential fields
                if title and company and link:
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "link": link,
                        "description": "",  # Will be filled by enrich_jobs()
                    })
                else:
                    logger.debug(
                        f"Skipping incomplete card: title={title}, "
                        f"company={company}, link={link}"
                    )

            except Exception as e:
                # If one card fails, skip it and continue with the rest
                logger.warning(f"Error parsing job card: {e}")
                continue

        return jobs

    def enrich_jobs(self, jobs):
        """Navigate to each job's dedicated page to scrape the full description.

        Indeed's individual job pages (/viewjob?jk=<jk>) render their
        description in a <div id="jobDescriptionText"> block.
        We use Selenium (already open) to load each page, which handles
        any JavaScript-rendered content.
<<<<<<< develop
        
        ANTI-DETECTION IMPROVEMENTS:
        - Increased random delays to avoid detection
        - Added human-like mouse movement simulation (via delay variation)
        """
        for i, job in enumerate(jobs):
            try:
                # Increase delays to appear more human-like
                delay = random_delay(2, 5)  # Was 1-3, now 2-5
=======
        """
        for i, job in enumerate(jobs):
            try:
                delay = random_delay(1, 3)
>>>>>>> main
                logger.info(
                    f"Fetching description {i + 1}/{len(jobs)} "
                    f"for '{job['title']}' (waited {delay:.1f}s)"
                )

                # Load the individual job page in the existing browser session
                self.driver.get(job["link"])
<<<<<<< develop
                random_delay(3, 6)  # Was 2-4, now 3-6 for better JS rendering
=======
                random_delay(2, 4)  # Let JS render
>>>>>>> main

                soup = BeautifulSoup(self.driver.page_source, "html.parser")

                # Primary selector — the main description container
                desc_div = soup.find("div", id="jobDescriptionText")
                if not desc_div:
                    # Fallback for newer layout
                    desc_div = soup.find("div", attrs={"data-testid": "jobsearch-JobComponent-description"})
                if not desc_div:
                    desc_div = soup.find("div", class_="jobsearch-jobDescriptionText")

                if desc_div:
                    job["description"] = desc_div.get_text(separator="\n", strip=True)
                else:
                    logger.warning(f"Could not find description block for {job['link']}")

            except Exception as e:
                logger.error(f"Failed to fetch description for {job['link']}: {e}")

        return jobs


# ── Helper ─────────────────────────────────────────────────────────────────

def _extract_jk(url):
    """Extract the job key ('jk') query parameter from an Indeed URL.

    Example:
        _extract_jk("https://www.indeed.com/rc/clk?jk=abc123&...") → "abc123"
    """
    try:
        params = parse_qs(urlparse(url).query)
        jk_values = params.get("jk")
        return jk_values[0] if jk_values else None
    except Exception:
        return None
