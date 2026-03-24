from django.core.management.base import BaseCommand
from scraping.models import JobListing
from deep_learning.nlp_pipeline import JobAnalyzer
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the NLP JobAnalyzer over all unprocessed job listings'

    def handle(self, *args, **options):
        # Fetch unprocessed jobs
        unprocessed_jobs = JobListing.objects.filter(nlp_processed=False, description__isnull=False).exclude(description='')
        
        if not unprocessed_jobs.exists():
            self.stdout.write(self.style.SUCCESS("No unprocessed jobs found!"))
            return
            
        self.stdout.write(self.style.HTTP_INFO(f"Found {unprocessed_jobs.count()} unprocessed jobs. Loading NLP models..."))
        
        # Initialize analyzer (this will take a moment the first time as it downloads/loads models to RAM)
        analyzer = JobAnalyzer()
        
        self.stdout.write(self.style.SUCCESS("Models loaded! Starting analysis..."))
        
        updated_count = 0
        for job in unprocessed_jobs:
            self.stdout.write(f"Analyzing: {job.title} at {job.company}...")
            
            try:
                is_relevant, score, skills = analyzer.analyze(job.description)
                
                # Update job
                job.is_relevant = is_relevant
                job.relevance_score = score
                job.extracted_skills = skills
                job.nlp_processed = True
                job.save()
                
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"  -> Relevant: {is_relevant} (Score: {score:.2f}) | Entities: {len(skills)} found"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> Failed to analyze: {e}"))
                logger.error(f"Analysis failed for job {job.id}", exc_info=True)
                
        self.stdout.write(self.style.SUCCESS(f"\n✅ Finished! Successfully analyzed {updated_count} jobs."))
