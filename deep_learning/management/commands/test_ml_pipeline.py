"""Management command for testing the ML pipeline on existing jobs."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from deep_learning.pipeline import BatchProcessor
from scraping.models import JobListing


class Command(BaseCommand):
    help = "Test and process existing unprocessed jobs using the core ML pipeline."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of unprocessed jobs to process.",
        )

    def handle(self, *args, **options) -> None:
        limit: int = options["limit"]
        queryset = JobListing.objects.filter(nlp_processed=False).exclude(description="")[:limit]
        total = queryset.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No unprocessed jobs found."))
            return

        self.stdout.write(self.style.HTTP_INFO(f"Processing {total} jobs..."))
        processor = BatchProcessor()

        def progress(job, result, idx, grand_total) -> None:
            status = "OK" if result["success"] else "FAIL"
            self.stdout.write(
                f"[{idx}/{grand_total}] {status} | Job #{job.id} | "
                f"score={result['relevance_score']:.3f} | "
                f"skills={len(result['extracted_skills'])}"
            )

        summary = processor.process_batch(queryset=queryset, callback=progress)
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("ML pipeline test completed."))
        self.stdout.write(
            f"Total={summary['total']} | Processed={summary['processed']} | "
            f"Success={summary['successful']} | Failed={summary['failed']} | "
            f"Relevant={summary['relevant_count']} | "
            f"AvgTimeMs={summary['avg_processing_time_ms']}"
        )
