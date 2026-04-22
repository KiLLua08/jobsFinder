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

    def handle(self, *args, **options):
        model_name = options['model_name']
        data_path = options['data_path']
        dry_run = options['dry_run']
        output_dir = os.path.join('deep_learning', 'saved_models', 'classifier_v1')

        if not os.path.exists(data_path):
            self.stdout.write(self.style.ERROR(f"Data file {data_path} not found. Did you run 'export_training_data' first?"))
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
            self.stdout.write(self.style.SUCCESS(f"Dry Run split: {len(train_indices)} Train | {len(val_indices)} Validation"))
            self.stdout.write("Exiting dry run.")
            return

        self.stdout.write(self.style.HTTP_INFO(f"Starting actual training pipeline for {model_name}..."))
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            run_training(
                jsonl_path=data_path,
                model_name=model_name,
                output_dir=output_dir
            )
            self.stdout.write(self.style.SUCCESS(f"Training completed successfully. Model saved to {output_dir}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Training failed: {str(e)}"))
