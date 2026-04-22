import os
import json
from django.core.management.base import BaseCommand
from scraping.models import JobListing

class Command(BaseCommand):
    help = 'Export human-labeled job listings to JSONL format for ML training'

    def handle(self, *args, **options):
        # Fetch labeled jobs
        labeled_jobs = JobListing.objects.filter(is_relevant_human_label__isnull=False, description__isnull=False).exclude(description='')

        if not labeled_jobs.exists():
            self.stdout.write(self.style.WARNING("No human-labeled jobs found! Please label some data first."))
            return

        export_dir = os.path.join('deep_learning', 'training_data')
        os.makedirs(export_dir, exist_ok=True)
        export_path = os.path.join(export_dir, 'dataset.jsonl')

        # Add gitkeep to ensure directory is tracked
        with open(os.path.join(export_dir, '.gitkeep'), 'w') as f:
            pass

        count = 0
        with open(export_path, 'w', encoding='utf-8') as f:
            for job in labeled_jobs:
                # Format required for our Dataset (1 for relevant, 0 for not relevant)
                label = 1 if job.is_relevant_human_label else 0
                
                # Create the JSON dict
                record = {
                    "text": job.description,
                    "label": label
                }
                
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully exported {count} labeled jobs to {export_path}"))
