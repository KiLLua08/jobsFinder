import json
import torch
from torch.utils.data import Dataset

class JobListingDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=512):
        """
        Reads a JSONL file and pre-tokenizes all items into memory.
        We do NOT use the Django ORM here to keep our ML pipelines decoupled
        and strictly reproducible based on exported static datasets.
        """
        self.texts = []
        self.labels = []
        
        # Read the file line by line
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                self.texts.append(record['text'])
                self.labels.append(record['label'])
                
        # Tokenize everything up front
        # For huge datasets you'd tokenize in __getitem__ or use Huggingface datasets
        # map() function, but since size is manageable here, we do it at init.
        self.encodings = tokenizer(
            self.texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt"
        )
        
    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: val[idx].clone().detach() for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item
