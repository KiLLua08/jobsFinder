from django.core.management.base import BaseCommand
from scraping.scraper import scrape_jobs

class Command(BaseCommand):
    help = 'Test the Selenium web scraper'

    def handle(self, *args, **options):
        self.stdout.write("Starting scraper for 'Data Scientist' jobs...")
        try:
            results = scrape_jobs("Data Scientist")
            self.stdout.write(self.style.SUCCESS(f"Successfully scraped {len(results)} jobs!"))
            for job in results:
                self.stdout.write(f"- {job['title']} at {job['company']}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error occurred: {e}"))
