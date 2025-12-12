"""
Data preparation and preprocessing for fine-tuning
"""

import json
import torch
from pathlib import Path
from typing import Dict, List
from transformers import AutoTokenizer, PreTrainedTokenizer

class GoldTrendDataset:
    """Dataset class for gold trend classification"""
    
    TREND_LABELS = {
        "up": 0,
        "down": 1,
        "sideways": 2
    }
    
    REVERSE_LABELS = {v: k for k, v in TREND_LABELS.items()}
    
    SYSTEM_PROMPT = """You are an expert gold market analyst. Analyze the given market commentary and classify the trend direction.

Respond with ONLY the trend classification in this format:
TREND: [uptrend/downtrend/sideways]
JUSTIFICATION: [Brief technical justification]"""
    
    def __init__(self, tokenizer: PreTrainedTokenizer, max_seq_length: int = 512):
        """
        Initialize dataset
        
        Args:
            tokenizer: HuggingFace tokenizer
            max_seq_length: Maximum sequence length for tokenization
        """
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length
        self.samples = []
    
    def load_from_jsonl(self, file_path: str):
        """Load samples from JSONL file"""
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    sample = json.loads(line)
                    self.samples.append(sample)
        print(f"Loaded {len(self.samples)} samples from {file_path}")
    
    def prepare_prompt(self, commentary: str, trend_label: str = None) -> str:
        """
        Prepare input prompt in conversational format
        
        Args:
            commentary: The market commentary text
            trend_label: Optional trend label for training
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""<|im_start|>system
{self.SYSTEM_PROMPT}<|im_end|>
<|im_start|>user
Market Commentary: {commentary}<|im_end|>
<|im_start|>assistant
"""
        
        if trend_label:
            response = f"TREND: {trend_label}\nJUSTIFICATION: Gold market showing {trend_label} trend based on technical analysis."
            prompt += response + "<|im_end|>"
        
        return prompt
    
    def tokenize_sample(self, sample: Dict, add_special_tokens: bool = True) -> Dict:
        """
        Tokenize a single sample
        
        Args:
            sample: Sample dictionary with 'commentary_text' and 'trend_label'
            add_special_tokens: Whether to add special tokens
        
        Returns:
            Tokenized sample
        """
        commentary = sample['commentary_text']
        trend_label = sample['trend_label']
        
        # Prepare prompt
        prompt = self.prepare_prompt(commentary, trend_label)
        
        # Tokenize
        encoding = self.tokenizer(
            prompt,
            max_length=self.max_seq_length,
            padding='max_length',
            truncation=True,
            add_special_tokens=add_special_tokens,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': encoding['input_ids'].squeeze(),
            'trend_label': self.TREND_LABELS[trend_label],
            'comment_id': sample['comment_id']
        }
    
    def prepare_training_data(self) -> List[Dict]:
        """
        Prepare all samples for training
        
        Returns:
            List of tokenized samples
        """
        tokenized_samples = []
        for i, sample in enumerate(self.samples):
            try:
                tokenized = self.tokenize_sample(sample)
                tokenized_samples.append(tokenized)
            except Exception as e:
                print(f"Error processing sample {i}: {e}")
        
        return tokenized_samples
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        return self.tokenize_sample(self.samples[idx])


class TrainingDataLoader:
    """Create training data loaders"""
    
    @staticmethod
    def create_torch_dataset(samples: List[Dict]) -> torch.utils.data.Dataset:
        """Convert samples to PyTorch dataset"""
        class SimpleDataset(torch.utils.data.Dataset):
            def __init__(self, samples):
                self.samples = samples
            
            def __len__(self):
                return len(self.samples)
            
            def __getitem__(self, idx):
                return self.samples[idx]
        
        return SimpleDataset(samples)
    
    @staticmethod
    def create_data_loaders(train_samples: List[Dict],
                           val_samples: List[Dict],
                           batch_size: int = 8) -> tuple:
        """
        Create train and validation data loaders
        
        Args:
            train_samples: Training samples
            val_samples: Validation samples
            batch_size: Batch size
        
        Returns:
            Tuple of (train_loader, val_loader)
        """
        train_dataset = TrainingDataLoader.create_torch_dataset(train_samples)
        val_dataset = TrainingDataLoader.create_torch_dataset(val_samples)
        
        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True
        )
        
        val_loader = torch.utils.data.DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False
        )
        
        return train_loader, val_loader


def prepare_dataset(data_dir: str, model_name: str, max_seq_length: int = 512) -> tuple:
    """
    Prepare complete dataset for training
    
    Args:
        data_dir: Directory containing JSONL data files
        model_name: Model name for tokenizer
        max_seq_length: Maximum sequence length
    
    Returns:
        Tuple of (train_dataset, val_dataset, test_dataset)
    """
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Create datasets
    train_dataset = GoldTrendDataset(tokenizer, max_seq_length)
    val_dataset = GoldTrendDataset(tokenizer, max_seq_length)
    test_dataset = GoldTrendDataset(tokenizer, max_seq_length)
    
    # Load data
    data_dir = Path(data_dir)
    train_dataset.load_from_jsonl(str(data_dir / "train.jsonl"))
    val_dataset.load_from_jsonl(str(data_dir / "validation.jsonl"))
    test_dataset.load_from_jsonl(str(data_dir / "test.jsonl"))
    
    return train_dataset, val_dataset, test_dataset


if __name__ == "__main__":
    # This is for testing data preparation
    from transformers import AutoTokenizer
    
    data_dir = Path(__file__).parent.parent / "data"
    model_name = "Qwen/Qwen2-7B-Instruct"
    
    print("Preparing dataset for fine-tuning...")
    train_ds, val_ds, test_ds = prepare_dataset(str(data_dir), model_name)
    
    print(f"\nDataset sizes:")
    print(f"  Train: {len(train_ds)}")
    print(f"  Val: {len(val_ds)}")
    print(f"  Test: {len(test_ds)}")
    
    # Show sample
    if len(train_ds) > 0:
        print("\nSample tokenized data:")
        sample = train_ds[0]
        print(f"  Input IDs shape: {sample['input_ids'].shape}")
        print(f"  Trend label: {sample['trend_label']}")
