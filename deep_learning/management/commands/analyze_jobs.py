import logging
from django.core.management.base import BaseCommand
from deep_learning.pipeline import BatchProcessor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the ML pipeline over all unprocessed job listings'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, help='Max jobs to process')

    def handle(self, *args, **options):
        from scraping.models import JobListing
        qs = JobListing.objects.filter(nlp_processed=False).exclude(description='')
        count = qs.count()

        if not count:
            self.stdout.write(self.style.SUCCESS('No unprocessed jobs found!'))
            return

        self.stdout.write(self.style.HTTP_INFO(f'Found {count} unprocessed jobs. Loading models...'))

        def _progress(job, res, idx, total):
            status = self.style.SUCCESS('✓') if res['success'] else self.style.ERROR('✗')
            self.stdout.write(
                f'  [{idx}/{total}] {status} {job.title} at {job.company} '
                f'| relevant={res["is_relevant"]} score={res["relevance_score"]:.2f} '
                f'skills={len(res["extracted_skills"])}'
            )

        processor = BatchProcessor()
        summary = processor.process_batch(queryset=qs, limit=options['limit'], callback=_progress)

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Done! {summary["successful"]}/{summary["total"]} processed, '
            f'{summary["relevant_count"]} relevant, '
            f'avg {summary["avg_processing_time_ms"]:.0f}ms/job'
        ))
