"""
Django management command to run scrapers.

Usage:
    python manage.py scrape --site linkedin --query "Data Scientist"
    python manage.py scrape --site linkedin --query "Python Developer" --pages 5
    python manage.py scrape --site linkedin --query "ML Engineer" --no-save
"""

from django.core.management.base import BaseCommand

from scraping.scrapers import LinkedInScraper
from scraping.utils.db import save_jobs_to_db


# Registry of available scrapers — add new ones here
SCRAPER_REGISTRY = {
    "linkedin": LinkedInScraper,
}


class Command(BaseCommand):
    help = "Run a job scraper and save results to the database"

    def add_arguments(self, parser):
        """Define the CLI arguments this command accepts."""
        parser.add_argument(
            "--site",
            type=str,
            choices=SCRAPER_REGISTRY.keys(),
            default="linkedin",
            help="Which site to scrape (default: linkedin)",
        )
        parser.add_argument(
            "--query",
            type=str,
            default="Data Scientist",
            help="Job search query (default: 'Data Scientist')",
        )
        parser.add_argument(
            "--pages",
            type=int,
            default=3,
            help="Number of pages to scrape (default: 3)",
        )
        parser.add_argument(
            "--no-save",
            action="store_true",
            help="Don't save to database, just print results",
        )

    def handle(self, *args, **options):
        site = options["site"]
        query = options["query"]
        pages = options["pages"]
        save = not options["no_save"]

        self.stdout.write(
            self.style.HTTP_INFO(
                f"🕷️  Scraping '{query}' from {site} ({pages} pages)..."
            )
        )

        # Create the scraper from the registry
        scraper_class = SCRAPER_REGISTRY[site]
        scraper = scraper_class(max_pages=pages)

        # Run the scraper
        jobs = scraper.run(query)

        if not jobs:
            self.stdout.write(self.style.WARNING("No jobs found!"))
            return

        # Display results
        self.stdout.write(self.style.SUCCESS(f"\n✅ Found {len(jobs)} jobs:\n"))
        for i, job in enumerate(jobs, 1):
            self.stdout.write(
                f"  {i}. {job['title']}\n"
                f"     📍 {job['company']} — {job.get('location', 'N/A')}\n"
                f"     🔗 {job['link'][:80]}...\n"
            )

        # Save to database
        if save:
            self.stdout.write("\n💾 Saving to database...")
            created, skipped = save_jobs_to_db(jobs)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done! {created} new jobs saved, {skipped} duplicates skipped."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("\n⏭️  --no-save flag set, skipping database save")
            )
