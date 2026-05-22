import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
from sklearn.model_selection import train_test_split
from .job_dataset import JobListingDataset
from .metrics import compute_metrics


def run_training(
    jsonl_path,
    model_name="distilroberta-base",
    output_dir="deep_learning/saved_models/classifier_v1",
) -> dict:
    """
    Main sequence classification fine-tuning training loop.
    Includes data splitting to avoid training on 100% of data.
    Implements memory-saving kwargs like gradient_accumulation_steps.

    Returns:
        dict of evaluation metrics from the best checkpoint.
    """
    print(f"Loading '{model_name}' tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Num labels corresponds to 2 classes (Relevant vs Not Relevant)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    print(f"Loading data from {jsonl_path}...")
    full_dataset = JobListingDataset(jsonl_path, tokenizer=tokenizer)

    # 85/15 Train-Validation split (Required to prevent overfitting evaluation)
    train_indices, val_indices = train_test_split(
        range(len(full_dataset)),
        test_size=0.15,
        random_state=42,            # Lock random seed for reproducibility
        stratify=full_dataset.labels  # Ensure label distribution is consistent across both splits
    )

    train_dataset = torch.utils.data.Subset(full_dataset, train_indices)
    val_dataset = torch.utils.data.Subset(full_dataset, val_indices)

    print(f"Train samples: {len(train_dataset)} | Val samples: {len(val_dataset)}")

    # Training Config using small batch sizes and accumulation for memory limits
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=4,      # Kept small to fit into average GPU VRAM
        per_device_eval_batch_size=4,
        gradient_accumulation_steps=4,      # Effective train batch size = 4 * 4 = 16
        fp16=torch.cuda.is_available(),     # 16-bit precision if CUDA is available
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir=os.path.join(output_dir, "logs"),
        logging_steps=10,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    print("Starting training...")
    trainer.train()

    print(f"Saving fine-tuned model to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("Training Complete!")

    # Return final evaluation metrics so the caller can persist them.
    metrics = trainer.evaluate()
    return metrics
