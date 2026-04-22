import os
import logging
from transformers import pipeline

logger = logging.getLogger(__name__)

class JobAnalyzer:
    _instance = None
    
    def __new__(cls):
        """Singleton pattern ensures we only load these huge models into RAM once."""
        if cls._instance is None:
            cls._instance = super(JobAnalyzer, cls).__new__(cls)
            cls._instance.is_finetuned = False
            cls._instance._initialize_pipelines()
        return cls._instance

    def _initialize_pipelines(self):
        logger.info("Initializing HuggingFace pipelines. This will use RAM and take a moment...")
        
        # Check if fine-tuned model exists
        model_path = os.path.join("deep_learning", "saved_models", "classifier_v1")
        if os.path.exists(model_path):
            logger.info(f"Loading custom fine-tuned model from {model_path}...")
            self.classifier = pipeline("text-classification", model=model_path, padding=True, truncation=True)
            self.is_finetuned = True
        else:
            logger.info("Custom model not found. Falling back to zero-shot distilroberta...")
            self.classifier = pipeline("zero-shot-classification", model="cross-encoder/nli-distilroberta-base")
            self.is_finetuned = False
        
        # Token classification pipeline for NER
        # (dslim/bert-base-NER is a standard NER. For real production, a skill-specific NER model is better)
        self.ner = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
        logger.info("Pipelines initialized.")

    def analyze(self, text):
        if not text:
            return False, 0.0, []
            
        # Truncate text to avoid hitting the 512 max length limit of typical BERT models
        truncated_text = text[:1500] 
        
        # 1. Classification
        if self.is_finetuned:
            result = self.classifier(truncated_text)[0]
            # Assumes output labels like 'LABEL_1' (Relevant) and 'LABEL_0' (Not Relevant)
            best_label = result['label']
            score = result['score']
            is_relevant = (best_label == 'LABEL_1' or best_label == '1')
        else:
            candidate_labels = ["Software Engineering or Data Science role", "Not related to Software or Data"]
            result = self.classifier(truncated_text, candidate_labels)
            best_label = result['labels'][0]
            score = result['scores'][0]
            is_relevant = (best_label == candidate_labels[0])
        
        # 2. Extract Entities (NER)
        entities = self.ner(truncated_text)
        skills = []
        for ent in entities:
            # Exclude random short tokens
            word = ent['word']
            if len(word) > 2 and word not in skills:
                skills.append(word)
                
        return is_relevant, score, skills
