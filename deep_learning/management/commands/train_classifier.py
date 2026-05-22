import os
import torch
from django.core.management.base import BaseCommand
from transformers import AutoTokenizer

from deep_learning.training.job_dataset import JobListingDataset
from deep_learning.training.train import run_training


class Command(BaseCommand):
    help = 'Train a Sequence Classification model on human-labeled JobListing objects.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model_name',
            type=str,
            default='distilroberta-base',
            help='Base HuggingFace model to fine-tune.'
        )
        parser.add_argument(
            '--data_path',
            type=str,
            default=os.path.join('deep_learning', 'training_data', 'dataset.jsonl'),
            help='Path to the exported JSONL training data.'
        )
        parser.add_argument(
            '--dry_run',
            action='store_true',
            help='Load and verify data but skip actual training loop.'
        )
        parser.add_argument(
            '--version',
            type=str,
            default=None,
            help='Version string for the saved model (e.g. 1.1.0). Auto-increments if omitted.'
        )

    def _next_version(self):
        """Return the next patch version based on existing MLModelMetadata records."""
        from deep_learning.models import MLModelMetadata
        latest = (
            MLModelMetadata.objects
            .filter(model_type="classifier")
            .order_by("-created_at")
            .first()
        )
        if not latest:
            return "1.0.0"
        try:
            major, minor, patch = latest.version.split(".")
            return f"{major}.{minor}.{int(patch) + 1}"
        except (ValueError, AttributeError):
            return "1.0.0"

    def handle(self, *args, **options):
        model_name = options['model_name']
        data_path = options['data_path']
        dry_run = options['dry_run']
        output_dir = os.path.join('deep_learning', 'saved_models', 'classifier_v1')

        if not os.path.exists(data_path):
            self.stdout.write(self.style.ERROR(
                f"Data file {data_path} not found. Did you run 'export_training_data' first?"
            ))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(f"--dry_run enabled. Simulating loading for: {model_name}"))
            from sklearn.model_selection import train_test_split
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            dataset = JobListingDataset(data_path, tokenizer=tokenizer)
            train_indices, val_indices = train_test_split(
                range(len(dataset)), test_size=0.15, random_state=42, stratify=dataset.labels
            )
            self.stdout.write(self.style.SUCCESS(f"Dataset successfully loaded! Total rows: {len(dataset)}"))
            self.stdout.write(self.style.SUCCESS(
                f"Dry Run split: {len(train_indices)} Train | {len(val_indices)} Validation"
            ))
            self.stdout.write("Exiting dry run.")
            return

        self.stdout.write(self.style.HTTP_INFO(f"Starting actual training pipeline for {model_name}..."))
        os.makedirs(output_dir, exist_ok=True)

        try:
            metrics = run_training(
                jsonl_path=data_path,
                model_name=model_name,
                output_dir=output_dir,
            )
            self.stdout.write(self.style.SUCCESS(
                f"Training completed successfully. Model saved to {output_dir}"
            ))

            # Record model metadata in the database.
            version = options['version'] or self._next_version()
            self._save_metadata(model_name, version, metrics)
            self.stdout.write(self.style.SUCCESS(f"Model metadata saved (version {version})."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Training failed: {str(e)}"))

    def _save_metadata(self, model_name: str, version: str, metrics: dict | None) -> None:
        """Persist MLModelMetadata for the newly trained classifier."""
        from django.utils import timezone
        from deep_learning.models import MLModelMetadata

        # Deactivate previous classifier versions.
        MLModelMetadata.objects.filter(model_type="classifier").update(is_active=False)

        accuracy = None
        f1 = None
        if metrics:
            # HuggingFace Trainer returns eval metrics keyed as eval_accuracy / eval_f1.
            accuracy = metrics.get("eval_accuracy") or metrics.get("accuracy")
            f1 = metrics.get("eval_f1") or metrics.get("f1")

        MLModelMetadata.objects.update_or_create(
            model_type="classifier",
            version=version,
            defaults={
                "name": f"RelevanceClassifier v{version}",
                "huggingface_model_id": model_name,
                "accuracy": accuracy,
                "f1_score": f1,
                "training_date": timezone.now(),
                "is_active": True,
            },
        )