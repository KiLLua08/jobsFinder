"""
BaseScraper — Abstract base class for all job scrapers.

DESIGN PATTERN: Template Method
--------------------------------
This uses the "Template Method" design pattern. The idea is:
  1. The BASE class defines the SKELETON of the scraping algorithm
     (setup browser → search → parse pages → save results)
  2. CHILD classes fill in the SPECIFIC details
     (what URL to hit, how to parse LinkedIn vs Indeed cards)

This way, all scrapers share the same anti-detection, retry logic,
and database saving — you only write the site-specific parsing code.

USAGE:
    class MyScaper(BaseScraper):
        def get_search_url(self, query, page): ...
        def parse_job_cards(self, page_source): ...

    scraper = MyScraper()
    jobs = scraper.run("Python Developer")
"""

import logging
import os
from abc import ABC, abstractmethod

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException

from scraping.utils.anti_detection import get_random_user_agent, random_delay

# Logger — prints structured messages instead of plain print()
# This is a best practice: logs can be filtered by level (INFO, WARNING, ERROR)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class that all site-specific scrapers inherit from.

    What it gives you for free:
    - Browser setup with anti-detection (random User-Agent)
    - Automatic retries on failure (with exponential backoff)
    - Pagination loop
    - Random delays between pages
    - Clean browser teardown

    What YOU must implement in your child class:
    - get_search_url(query, page)  → the URL to scrape
    - parse_job_cards(page_source) → extract jobs from HTML
    """

    def __init__(self, max_pages=3, max_retries=3):
        """
        Args:
            max_pages:   How many pages of results to scrape (default 3)
            max_retries: How many times to retry a failed page (default 3)
        """
        self.max_pages = max_pages
        self.max_retries = max_retries
        self.driver = None  # Will hold the Selenium WebDriver instance

    # ── Browser Setup & Teardown ─────────────────────────────────

    def _create_driver(self):
        """Create a Selenium WebDriver with anti-detection options.

        WHAT HAPPENS HERE:
        1. We set Chrome to run headless (no visible window)
        2. We set a random User-Agent so each session looks different
        3. We disable automation flags that websites check for
        4. We connect to the Selenium container running in Docker
        """
        options = ChromeOptions()
        options.add_argument("--headless=new")    # Run without a window
        options.add_argument("--no-sandbox")       # Required in Docker
        options.add_argument("--disable-dev-shm-usage")  # Prevent crashes

        # Anti-detection: set a random real-browser User-Agent
        user_agent = get_random_user_agent()
        options.add_argument(f"--user-agent={user_agent}")
        logger.info(f"Using User-Agent: {user_agent[:50]}...")

        # Anti-detection: remove the "Chrome is being controlled by
        # automated software" banner and related flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Connect to the Selenium Hub (the 'chrome' Docker container)
        # In Docker: http://chrome:4444/wd/hub
        # Locally:   http://localhost:4444/wd/hub
        selenium_host = os.environ.get("SELENIUM_HOST", "localhost")
        remote_url = f"http://{selenium_host}:4444/wd/hub"

        self.driver = webdriver.Remote(
            command_executor=remote_url,
            options=options,
        )

        # Set a page load timeout so we don't hang forever
        self.driver.set_page_load_timeout(30)
        logger.info(f"Browser connected to {remote_url}")

    def _quit_driver(self):
        """Safely close the browser and free resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass  # Don't crash if the browser is already gone
            finally:
                self.driver = None

    # ── Abstract Methods (child classes MUST implement these) ────

    @abstractmethod
    def get_search_url(self, query, page=1):
        """Return the URL to scrape for a given search query and page number.

        Example:
            return f"https://linkedin.com/jobs?keywords={query}&start={page * 25}"
        """
        pass

    @abstractmethod
    def parse_job_cards(self, page_source):
        """Parse the HTML page source and return a list of job dicts.

        Each dict should have at minimum:
            {"title": str, "company": str, "link": str}

        Optional fields:
            "location", "description"

        Args:
            page_source: Raw HTML string from the browser

        Returns:
            List of dicts, one per job found on the page
        """
        pass

    def enrich_jobs(self, jobs):
        """Hook to fetch additional details (like full descriptions) for each job.
        
        Child classes can override this to navigate to individual job links
        and extract more text. By default, it just returns the jobs as-is.
        """
        return jobs

    # ── Core Scraping Logic ──────────────────────────────────────

    def _fetch_page(self, url):
        """Load a URL in the browser with retry logic.

        RETRY WITH EXPONENTIAL BACKOFF:
        If a page fails to load, we don't immediately give up. Instead:
          - Attempt 1: wait 2s, try again
          - Attempt 2: wait 4s, try again
          - Attempt 3: wait 8s, try again
        Each wait is DOUBLED — this is "exponential backoff".
        It gives the server time to recover if it's overloaded.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                self.driver.get(url)
                # Wait for page to load (random delay mimics human)
                random_delay(3, 6)
                return self.driver.page_source

            except WebDriverException as e:
                wait_time = 2 ** attempt  # 2, 4, 8 seconds
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed for {url}: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                random_delay(wait_time, wait_time + 2)

        logger.error(f"All {self.max_retries} attempts failed for {url}")
        return None

    def run(self, query):
        """Execute the full scraping pipeline.

        This is the TEMPLATE METHOD — it defines the algorithm:
          1. Start browser
          2. For each page: fetch → parse → collect jobs
          3. Close browser
          4. Return all jobs

        Args:
            query: Search term (e.g., "Data Scientist")

        Returns:
            List of job dicts
        """
        all_jobs = []

        try:
            # Step 1: Start the browser
            self._create_driver()
            logger.info(f"Starting scrape for: '{query}'")

            # Step 2: Loop through pages
            for page in range(1, self.max_pages + 1):
                url = self.get_search_url(query, page)
                logger.info(f"Scraping page {page}/{self.max_pages}: {url}")

                # Fetch the page HTML
                page_source = self._fetch_page(url)
                if not page_source:
                    logger.warning(f"Skipping page {page} — failed to load")
                    continue

                # Parse job cards from the HTML
                jobs = self.parse_job_cards(page_source)
                logger.info(f"Found {len(jobs)} jobs on page {page}")

                # If we got 0 jobs, we've probably hit the last page
                if not jobs:
                    logger.info("No more jobs found, stopping pagination")
                    break

                # Fetch extra details (like full descriptions) for these jobs
                jobs = self.enrich_jobs(jobs)

                all_jobs.extend(jobs)

                # Random delay between pages (anti-detection)
                if page < self.max_pages:
                    delay = random_delay(2, 5)
                    logger.info(f"Waiting {delay:.1f}s before next page...")

        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)

        finally:
            # Step 3: Always close the browser, even if something crashed
            self._quit_driver()

        logger.info(f"Scraping complete. Total jobs found: {len(all_jobs)}")
        return all_jobs
