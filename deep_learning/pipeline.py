"""Core ML pipeline for job relevance + skills extraction."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

CLASSIFIER_MODEL_ID = "facebook/bart-large-mnli"
NER_MODEL_ID = "dslim/bert-base-NER"
MODEL_VERSION = "1.0.0"

TECH_SKILLS: set[str] = {
    "python", "sql", "aws", "tensorflow", "django", "react", "pytorch", "docker",
    "kubernetes", "fastapi", "flask", "java", "javascript", "typescript", "postgresql",
    "mysql", "mongodb", "redis", "spark", "airflow", "git", "linux", "azure", "gcp",
    "scikit-learn", "numpy", "pandas", "rest", "graphql", "terraform", "jenkins",
}

def _skills_pattern() -> re.Pattern[str]:
    escaped = [re.escape(s) for s in sorted(TECH_SKILLS, key=len, reverse=True)]
    return re.compile(r"\b(?:" + "|".join(escaped) + r")\b", flags=re.IGNORECASE)


SKILLS_PATTERN = _skills_pattern()


class ModelCache:
    """Singleton cache to avoid reloading transformer models per request."""

    _instance: Optional["ModelCache"] = None
    _classifier: Any = None
    _ner: Any = None
    _initialized: bool = False

    def __new__(cls) -> "ModelCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        if self._initialized:
            return
        self._load_classifier()
        self._load_ner()
        self._initialized = True
        logger.info("ML model cache initialized.")

    def _load_classifier(self) -> None:
        from transformers import pipeline as hf_pipeline

        local_model = os.path.join("deep_learning", "saved_models", "classifier_v1")
        model_id = local_model if os.path.exists(local_model) else CLASSIFIER_MODEL_ID
        logger.info("Loading classifier model: %s", model_id)
        self._classifier = hf_pipeline(
            task="zero-shot-classification",
            model=model_id,
            truncation=True,
            max_length=512,
        )

    def _load_ner(self) -> None:
        from transformers import pipeline as hf_pipeline

        logger.info("Loading token classification model: %s", NER_MODEL_ID)
        self._ner = hf_pipeline(
            task="ner",
            model=NER_MODEL_ID,
            aggregation_strategy="simple",
        )

    @property
    def classifier(self):
        if self._classifier is None:
            self._load_classifier()
        return self._classifier

    @property
    def ner(self):
        if self._ner is None:
            self._load_ner()
        return self._ner

    def classifier_name(self) -> str:
        local_model = os.path.join("deep_learning", "saved_models", "classifier_v1")
        return local_model if os.path.exists(local_model) else CLASSIFIER_MODEL_ID


class RelevanceClassifier:
    """Binary relevance classifier with normalized confidence score."""

    def __init__(self) -> None:
        self._cache = ModelCache()

    def classify(self, text: str) -> tuple[bool, float]:
        if not text or not text.strip():
            return False, 0.0

        snippet = text[:1000]
        try:
            candidate_labels = ["relevant job posting", "irrelevant content", "spam"]
            pred = self._cache.classifier(
                snippet,
                candidate_labels,
                multi_label=False,
            )
            labels = pred.get("labels", [])
            scores = pred.get("scores", [])

            relevant_score = 0.0
            if "relevant job posting" in labels:
                idx = labels.index("relevant job posting")
                relevant_score = float(scores[idx])

            relevance_score = round(relevant_score, 4)
            is_relevant = relevance_score >= 0.55
            return is_relevant, relevance_score
        except Exception as exc:
            logger.exception("Classification failed: %s", exc)
            return False, 0.0


class SkillsExtractor:
    """Hybrid skill extractor (regex vocabulary + token classification)."""

    def __init__(self) -> None:
        self._cache = ModelCache()

    def extract(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        skills: set[str] = set()
        snippet = text[:3000]

        for match in SKILLS_PATTERN.findall(snippet):
            skills.add(self._normalize_skill(match))

        try:
            entities = self._cache.ner(snippet)
            for entity in entities:
                token = str(entity.get("word", "")).strip()
                if not token or len(token) < 2 or token.startswith("##"):
                    continue
                if token.lower() in TECH_SKILLS:
                    skills.add(self._normalize_skill(token))
        except Exception as exc:
            logger.warning("NER extraction degraded to regex-only: %s", exc)

        return sorted(skills)

    @staticmethod
    def _normalize_skill(value: str) -> str:
        low = value.strip().lower()
        if low in {"sql", "aws", "gcp", "api", "ml", "ai"}:
            return low.upper()
        if low in {"javascript", "typescript"}:
            return low.title()
        return low.capitalize()


class BatchProcessor:
    """Process one or many JobListing records through the ML pipeline."""

    def __init__(self) -> None:
        self.classifier = RelevanceClassifier()
        self.extractor = SkillsExtractor()
        self.cache = ModelCache()

    def process_single(self, job) -> dict[str, Any]:
        start = time.time()
        result: dict[str, Any] = {
            "job_id": job.id,
            "success": False,
            "is_relevant": False,
            "relevance_score": 0.0,
            "extracted_skills": [],
            "processing_time_ms": 0.0,
            "error": "",
        }

        try:
            description = (job.description or "").strip()
            if not description:
                result["error"] = "Missing description"
                return result

            is_relevant, score = self.classifier.classify(description)
            skills = self.extractor.extract(description)

            result.update(
                success=True,
                is_relevant=is_relevant,
                relevance_score=score,
                extracted_skills=skills,
            )
        except Exception as exc:
            logger.exception("Single job processing failed for %s: %s", job.id, exc)
            result["error"] = str(exc)
        finally:
            result["processing_time_ms"] = round((time.time() - start) * 1000, 2)
        return result

    def process_batch(
        self,
        queryset=None,
        limit: Optional[int] = None,
        callback=None,
    ) -> dict[str, Any]:
        from deep_learning.models import InferenceLog
        from scraping.models import JobListing

        if queryset is None:
            queryset = JobListing.objects.filter(nlp_processed=False).exclude(description="")
        if limit:
            queryset = queryset[:limit]

        jobs = list(queryset)
        summary: dict[str, Any] = {
            "total": len(jobs),
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "relevant_count": 0,
            "avg_processing_time_ms": 0.0,
        }

        total_ms = 0.0
        for idx, job in enumerate(jobs, start=1):
            res = self.process_single(job)
            total_ms += res["processing_time_ms"]
            summary["processed"] += 1

            if res["success"]:
                job.is_relevant = res["is_relevant"]
                job.relevance_score = res["relevance_score"]
                job.extracted_skills = res["extracted_skills"]
                job.nlp_processed = True
                job.save(update_fields=["is_relevant", "relevance_score", "extracted_skills", "nlp_processed"])
                summary["successful"] += 1
                if res["is_relevant"]:
                    summary["relevant_count"] += 1
            else:
                summary["failed"] += 1

            try:
                InferenceLog.objects.create(
                    job_listing=job,
                    model_used=self.cache.classifier_name(),
                    model_version=MODEL_VERSION,
                    inference_type="full",
                    is_relevant=res["is_relevant"] if res["success"] else None,
                    relevance_score=res["relevance_score"] if res["success"] else None,
                    extracted_skills=res["extracted_skills"] if res["success"] else [],
                    processing_time_ms=res["processing_time_ms"],
                    success=res["success"],
                    error_message=res["error"],
                )
            except Exception as exc:
                logger.warning("Failed creating inference log for job %s: %s", job.id, exc)

            if callback:
                callback(job, res, idx, len(jobs))

        if summary["processed"]:
            summary["avg_processing_time_ms"] = round(total_ms / summary["processed"], 2)
        return summary
