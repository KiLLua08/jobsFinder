"""
Django models for the deep_learning app.

Stores ML model metadata (versions, accuracy, training dates) and
inference logs for auditing and performance monitoring.
"""

from django.db import models
from django.utils import timezone


class MLModelMetadata(models.Model):
    """
    Tracks metadata about each ML model version deployed in the pipeline.

    This allows the system to keep a history of model versions, their
    performance metrics, and which model is currently active.
    """

    MODEL_TYPE_CHOICES = [
        ("classifier", "Relevance Classifier"),
        ("ner", "Skills Extractor (NER)"),
    ]

    name = models.CharField(
        max_length=255,
        help_text="Human-readable model name, e.g. 'RelevanceClassifier v2'"
    )
    model_type = models.CharField(
        max_length=20,
        choices=MODEL_TYPE_CHOICES,
        help_text="The type of model (classifier or NER)"
    )
    version = models.CharField(
        max_length=50,
        help_text="Semantic version string, e.g. '1.0.0'"
    )
    huggingface_model_id = models.CharField(
        max_length=255,
        help_text="HuggingFace model identifier, e.g. 'distilbert-base-uncased'"
    )
    accuracy = models.FloatField(
        null=True, blank=True,
        help_text="Model accuracy on the evaluation set (0.0 - 1.0)"
    )
    f1_score = models.FloatField(
        null=True, blank=True,
        help_text="Model F1 score on the evaluation set (0.0 - 1.0)"
    )
    training_date = models.DateTimeField(
        null=True, blank=True,
        help_text="When this model version was trained"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this model version is currently active"
    )
    notes = models.TextField(
        blank=True, default="",
        help_text="Free-form notes about this model version"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ML Model Metadata"
        verbose_name_plural = "ML Model Metadata"
        ordering = ["-created_at"]
        unique_together = ["model_type", "version"]

    def __str__(self) -> str:
        return f"{self.name} v{self.version} ({'active' if self.is_active else 'inactive'})"


class InferenceLog(models.Model):
    """
    Records every ML inference call for auditing, debugging,
    and performance monitoring.
    """

    job_listing = models.ForeignKey(
        "scraping.JobListing",
        on_delete=models.CASCADE,
        related_name="inference_logs",
        help_text="The job listing that was processed"
    )
    model_used = models.CharField(
        max_length=255,
        help_text="Identifier of the model used for this inference"
    )
    model_version = models.CharField(
        max_length=50,
        default="1.0.0",
        help_text="Version of the model used"
    )
    inference_type = models.CharField(
        max_length=20,
        choices=[
            ("classification", "Classification"),
            ("ner", "Named Entity Recognition"),
            ("full", "Full Pipeline"),
        ],
        default="full",
        help_text="Type of inference performed"
    )
    is_relevant = models.BooleanField(
        null=True, blank=True,
        help_text="Classification result: relevant or not"
    )
    relevance_score = models.FloatField(
        null=True, blank=True,
        help_text="Confidence score (0.0 - 1.0)"
    )
    extracted_skills = models.JSONField(
        default=list, blank=True,
        help_text="Skills extracted by NER"
    )
    processing_time_ms = models.FloatField(
        null=True, blank=True,
        help_text="Time taken for inference in milliseconds"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether inference completed successfully"
    )
    error_message = models.TextField(
        blank=True, default="",
        help_text="Error message if inference failed"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When this inference was performed"
    )

    class Meta:
        verbose_name = "Inference Log"
        verbose_name_plural = "Inference Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["job_listing", "-timestamp"]),
            models.Index(fields=["model_used"]),
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"[{status}] Job #{self.job_listing_id} | {self.model_used} @ {self.timestamp:%Y-%m-%d %H:%M}"
