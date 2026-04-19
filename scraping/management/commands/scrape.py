"""
Django management command to run scrapers.

Usage:
    python manage.py scrape --site linkedin --query "Data Scientist"
    python manage.py scrape --site indeed --query "Python Developer" --pages 5
    python manage.py scrape --site all --query "ML Engineer"  # Scrape all sites
    python manage.py scrape --site linkedin --query "Data" --no-save
    python manage.py scrape --site all --query "Data" --clear-before  # Clear DB first
"""

from django.core.management.base import BaseCommand

from scraping.scrapers import LinkedInScraper, IndeedScraper
from scraping.utils.db import save_jobs_to_db


# Registry of available scrapers — add new ones here
SCRAPER_REGISTRY = {
    "linkedin": LinkedInScraper,
    "indeed": IndeedScraper,
}


class Command(BaseCommand):
    help = "Run a job scraper and save results to the database"

    def add_arguments(self, parser):
        """Define the CLI arguments this command accepts."""
        # Get available site choices and add 'all' option
        site_choices = list(SCRAPER_REGISTRY.keys()) + ['all']

        parser.add_argument(
            "--site",
            type=str,
            choices=site_choices,
            default="linkedin",
            help="Which site to scrape (default: linkedin). Use 'all' to scrape all sites.",
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
        parser.add_argument(
            "--clear-before",
            action="store_true",
            help="Clear all existing jobs before scraping (use with caution)",
        )

    def handle(self, *args, **options):
        site = options["site"]
        query = options["query"]
        pages = options["pages"]
        save = not options["no_save"]
        clear_before = options["clear_before"]

        # Optional: Clear database before scraping
        if clear_before:
            from scraping.models import JobListing
            count = JobListing.objects.count()
            JobListing.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"🗑️  Cleared {count} existing jobs from database")
            )

        # Determine which sites to scrape
        if site == "all":
            sites_to_scrape = list(SCRAPER_REGISTRY.keys())
        else:
            sites_to_scrape = [site]

        total_created = 0
        total_skipped = 0

        for site_name in sites_to_scrape:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"\n🕷️  Scraping '{query}' from {site_name} ({pages} pages)..."
                )
            )

            # Create the scraper from the registry
            scraper_class = SCRAPER_REGISTRY[site_name]
            scraper = scraper_class(max_pages=pages)

            # Run the scraper
            jobs = scraper.run(query)

            if not jobs:
                self.stdout.write(self.style.WARNING(f"No jobs found on {site_name}!"))
                continue

            # Display results
            self.stdout.write(self.style.SUCCESS(f"\n✅ Found {len(jobs)} jobs on {site_name}:\n"))
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
                total_created += created
                total_skipped += skipped
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Done! {created} new jobs saved, {skipped} duplicates skipped."
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING("\n⏭️  --no-save flag set, skipping database save")
                )

        # Final summary
        if save:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🎉 Total: {total_created} new jobs saved, {total_skipped} duplicates skipped."
                )
            )