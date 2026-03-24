"""
LinkedInScraper — Scrapes job listings from LinkedIn's public job search.

This class inherits from BaseScraper and only needs to implement:
  1. get_search_url()  → builds the LinkedIn search URL
  2. parse_job_cards() → extracts job data from LinkedIn's HTML

Everything else (browser, retries, anti-detection, pagination)
is handled by the parent BaseScraper class.
"""

import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn's public job search page.

    NOTE: LinkedIn's public search page (no login required) uses
    CSS classes like 'base-card', 'base-search-card__title', etc.
    These may change over time — if scraping breaks, check the
    class names first.
    """

    # LinkedIn shows 25 jobs per page
    JOBS_PER_PAGE = 25

    def get_search_url(self, query, page=1):
        """Build the LinkedIn job search URL.

        LinkedIn's public job search uses this URL pattern:
          https://www.linkedin.com/jobs/search/?keywords=<query>&start=<offset>

        The 'start' parameter controls pagination:
          Page 1 → start=0
          Page 2 → start=25
          Page 3 → start=50

        quote_plus() encodes the query for URLs:
          "Data Scientist" → "Data+Scientist"
        """
        encoded_query = quote_plus(query)
        offset = (page - 1) * self.JOBS_PER_PAGE
        return (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={encoded_query}&start={offset}"
        )

    def parse_job_cards(self, page_source):
        """Extract job listings from LinkedIn's HTML.

        HOW THIS WORKS:
        1. BeautifulSoup parses the raw HTML into a tree structure
        2. We find all <div> tags with class 'base-card' (each = one job)
        3. From each card, we extract title, company, location, and link
        4. We return a list of dicts

        DEFENSIVE PARSING:
        We use .find() which returns None if not found, and we check
        for None before calling .text — this prevents crashes if
        LinkedIn changes their HTML structure.
        """
        soup = BeautifulSoup(page_source, "html.parser")
        job_cards = soup.find_all("div", class_="base-card")
        jobs = []

        for card in job_cards:
            try:
                # Extract title
                title_tag = card.find("h3", class_="base-search-card__title")
                title = title_tag.text.strip() if title_tag else None

                # Extract company name
                company_tag = card.find("h4", class_="base-search-card__subtitle")
                company = company_tag.text.strip() if company_tag else None

                # Extract location
                location_tag = card.find("span", class_="job-search-card__location")
                location = location_tag.text.strip() if location_tag else None

                # Extract job link
                link_tag = card.find("a", class_="base-card__full-link")
                link = link_tag["href"] if link_tag else None

                # Only add if we have the essential fields
                if title and company and link:
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location or "",
                        "link": link,
                        "description": "",  # Will be filled later
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
        """Navigate to each job's dedicated page to scrape the full description."""
        import urllib.request
        from scraping.utils.anti_detection import get_random_user_agent, random_delay

        for i, job in enumerate(jobs):
            try:
                # Add a delay between resolving each job URL
                delay = random_delay(1, 3)
                logger.info(f"Fetching description {i+1}/{len(jobs)} for {job['title']} (waited {delay:.1f}s)")
                
                # We use raw urllib here because LinkedIn's bot detection 
                # aggressively blocks Selenium Headless browsers on individual job pages,
                # but often allows raw HTTP requests with a normal User-Agent!
                req = urllib.request.Request(
                    job["link"], 
                    headers={'User-Agent': get_random_user_agent()}
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    page_source = response.read().decode('utf-8')
                    
                soup = BeautifulSoup(page_source, "html.parser")
                
                # The description block in public LinkedIn jobs
                desc_div = soup.find("div", class_="show-more-less-html__markup")
                if not desc_div:
                    desc_div = soup.find("div", class_="description__text")
                    
                if desc_div:
                    job["description"] = desc_div.get_text(separator="\n", strip=True)
                else:
                    logger.warning(f"Could not find description block for {job['link']}")
                    
            except Exception as e:
                logger.error(f"Failed to fetch description for {job['link']}: {e}")
                
        return jobs
