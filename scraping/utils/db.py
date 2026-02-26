"""
Database helper for saving scraped jobs.

Separates the "save to DB" logic from the scrapers themselves.
This follows the Single Responsibility Principle — scrapers scrape,
this module saves.
"""

import logging

from scraping.models import JobListing

logger = logging.getLogger(__name__)


def save_jobs_to_db(jobs_data):
    """Save a list of job dicts to the database.

    Uses get_or_create() which does:
      - If a job with this link already exists → skip it (no duplicate)
      - If it's new → create it

    The 'link' field has unique=True in the model, so this is safe.

    Args:
        jobs_data: List of dicts with keys: title, company, location, link, description

    Returns:
        Tuple of (created_count, skipped_count)
    """
    created = 0
    skipped = 0

    for job in jobs_data:
        try:
            _, was_created = JobListing.objects.get_or_create(
                link=job["link"],  # Look up by this field
                defaults={         # Only used if creating a new record
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "description": job.get("description", ""),
                },
            )

            if was_created:
                created += 1
            else:
                skipped += 1

        except Exception as e:
            logger.error(f"Failed to save job '{job.get('title')}': {e}")
            skipped += 1

    logger.info(f"Saved {created} new jobs, skipped {skipped} duplicates")
    return created, skipped
