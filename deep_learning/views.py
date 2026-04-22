"""REST API endpoints for ML pipeline operations."""

from __future__ import annotations

import json
import logging
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from deep_learning.pipeline import BatchProcessor, ModelCache, RelevanceClassifier, SkillsExtractor
from scraping.models import JobListing

logger = logging.getLogger(__name__)


def _parse_json_body(request: HttpRequest) -> dict[str, Any]:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


@csrf_exempt
@require_POST
def classify_job(request: HttpRequest) -> JsonResponse:
    """Classify one job description and extract technical skills."""
    payload = _parse_json_body(request)
    description = str(payload.get("description", "")).strip()
    if not description:
        return JsonResponse({"error": "description is required"}, status=400)

    try:
        classifier = RelevanceClassifier()
        extractor = SkillsExtractor()
        is_relevant, score = classifier.classify(description)
        skills = extractor.extract(description)
        return JsonResponse(
            {
                "is_relevant": is_relevant,
                "relevance_score": score,
                "extracted_skills": skills,
            },
            status=200,
        )
    except Exception as exc:
        logger.exception("Classification API failure: %s", exc)
        return JsonResponse({"error": "classification failed"}, status=500)


@require_GET
def ml_stats(request: HttpRequest) -> JsonResponse:
    """Return processing progress for all job listings."""
    total = JobListing.objects.count()
    processed = JobListing.objects.filter(nlp_processed=True).count()
    relevant = JobListing.objects.filter(nlp_processed=True, is_relevant=True).count()
    pct = round((processed / total) * 100, 2) if total else 0.0
    return JsonResponse(
        {
            "total": total,
            "processed": processed,
            "relevant": relevant,
            "percentage": pct,
        }
    )


@csrf_exempt
@require_POST
def process_batch(request: HttpRequest) -> JsonResponse:
    """Process unprocessed jobs in batch mode."""
    payload = _parse_json_body(request)
    limit_value = payload.get("limit")
    limit = int(limit_value) if isinstance(limit_value, int) or (isinstance(limit_value, str) and limit_value.isdigit()) else None

    try:
        processor = BatchProcessor()
        summary = processor.process_batch(limit=limit)
        return JsonResponse(summary, status=200)
    except Exception as exc:
        logger.exception("Batch processing API failure: %s", exc)
        return JsonResponse({"error": "batch processing failed"}, status=500)


@require_GET
def ml_health(request: HttpRequest) -> JsonResponse:
    """Check model loading status and availability."""
    cache = ModelCache()
    classifier_loaded = cache._classifier is not None
    ner_loaded = cache._ner is not None
    return JsonResponse(
        {
            "status": "ok",
            "cache_initialized": cache.initialized,
            "classifier_loaded": classifier_loaded,
            "ner_loaded": ner_loaded,
        }
    )
