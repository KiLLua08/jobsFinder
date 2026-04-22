import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def compute_metrics(eval_pred):
    """
    Computes accuracy, precision, recall, and f1 score during validation/evaluation.
    
    Args:
        eval_pred: An EvalPrediction object containing predictions and label_ids
    """
    predictions, labels = eval_pred
    
    # Argmax to get the predicted class index (0 or 1)
    preds = np.argmax(predictions, axis=1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="binary")
    acc = accuracy_score(labels, preds)
    
    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }
