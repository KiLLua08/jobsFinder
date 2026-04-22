"""Signals for automatic ML processing on job save events."""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="scraping.JobListing")
def auto_process_job_listing(sender, instance, created, **kwargs):
    """Auto-process non-processed jobs and persist ML fields."""
    if instance.nlp_processed:
        return

    if not instance.description or not instance.description.strip():
        logger.debug("Skipping ML processing for job %s: no description", instance.id)
        return

    try:
        from deep_learning.models import InferenceLog
        from deep_learning.pipeline import BatchProcessor
        from scraping.models import JobListing

        processor = BatchProcessor()
        result = processor.process_single(instance)

        JobListing.objects.filter(pk=instance.pk).update(
            is_relevant=result["is_relevant"] if result["success"] else False,
            relevance_score=result["relevance_score"] if result["success"] else 0.0,
            extracted_skills=result["extracted_skills"] if result["success"] else [],
            nlp_processed=True,
        )

        InferenceLog.objects.create(
            job_listing=instance,
            model_used=processor.cache.classifier_name(),
            model_version="1.0.0",
            inference_type="full",
            is_relevant=result["is_relevant"] if result["success"] else None,
            relevance_score=result["relevance_score"] if result["success"] else None,
            extracted_skills=result["extracted_skills"] if result["success"] else [],
            processing_time_ms=result["processing_time_ms"],
            success=result["success"],
            error_message=result["error"],
        )
        logger.info("Auto-processed job %s with success=%s", instance.id, result["success"])
    except Exception as exc:
        logger.error("Auto-processing failed for job %s: %s", instance.id, exc, exc_info=True)
