"""
Fine-tuning script using LoRA for efficient training
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

import torch
import yaml
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset

from data_preparation import prepare_dataset, GoldTrendDataset


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def setup_model_and_tokenizer(model_name: str, config: dict):
    """
    Setup model with tokenizer and optional 4-bit quantization.
    Falls back to FP16/FP32 when bitsandbytes or CUDA is unavailable.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Determine quantization usage
    use_bnb_env = os.environ.get("USE_BNB_4BIT", "1") == "1"
    use_bnb = False
    quant_config = None

    if use_bnb_env and torch.cuda.is_available():
        try:
            import bitsandbytes as _  # noqa: F401
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            use_bnb = True
        except ImportError:
            print("[warn] bitsandbytes not available; falling back to non-quantized load.")

    model_kwargs = {
        "trust_remote_code": True,
    }

    if use_bnb and quant_config:
        model_kwargs.update({
            "quantization_config": quant_config,
            "device_map": "auto",
            "attn_implementation": "flash_attention_2" if torch.cuda.is_available() else None,
        })
    elif torch.cuda.is_available():
        # GPU present but no bnb; use half precision
        model_kwargs.update({
            "torch_dtype": torch.float16,
            "device_map": "auto",
            "attn_implementation": "flash_attention_2",
        })
    else:
        # CPU/MPS fallback: stay on CPU to avoid mps autocast issues
        model_kwargs.update({
            "torch_dtype": torch.float32,
            "device_map": None,
            "attn_implementation": None,
        })

    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)

    if use_bnb:
        model = prepare_model_for_kbit_training(model)

    return model, tokenizer


def setup_lora(model, config: dict):
    """
    Setup LoRA for efficient fine-tuning
    
    Args:
        model: Base model
        config: Configuration dictionary
    
    Returns:
        Model with LoRA adapters
    """
    lora_config = LoraConfig(
        r=config['lora']['r'],
        lora_alpha=config['lora']['lora_alpha'],
        lora_dropout=config['lora']['lora_dropout'],
        bias=config['lora']['bias'],
        task_type=config['lora']['task_type'],
        target_modules=config['lora']['target_modules'],
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model


def convert_dataset_to_hf(samples: list, tokenizer) -> Dataset:
    """
    Convert dataset to HuggingFace Dataset format
    
    Args:
        samples: List of sample dictionaries
        tokenizer: Tokenizer instance
    
    Returns:
        HuggingFace Dataset
    """
    def preprocess_function(example):
        commentary = example['commentary_text']
        trend_label = example['trend_label']
        
        # Prepare prompt
        prompt = f"""<|im_start|>system
You are an expert gold market analyst. Analyze the given market commentary and classify the trend direction.
Respond with ONLY the trend classification in this format:
TREND: [uptrend/downtrend/sideways]
JUSTIFICATION: [Brief technical justification]<|im_end|>
<|im_start|>user
Market Commentary: {commentary}<|im_end|>
<|im_start|>assistant
TREND: {trend_label}
JUSTIFICATION: Gold market analysis indicates {trend_label} trend based on technical indicators.<|im_end|>"""
        
        # Tokenize
        encoding = tokenizer(
            prompt,
            max_length=512,
            truncation=True,
            padding="max_length"
        )
        
        return {
            'input_ids': encoding['input_ids'],
            'attention_mask': encoding['attention_mask'],
            'labels': encoding['input_ids']
        }
    
    # Convert to Dataset
    dataset_dict = {
        'comment_id': [s['comment_id'] for s in samples],
        'commentary_text': [s['commentary_text'] for s in samples],
        'trend_label': [s['trend_label'] for s in samples],
    }
    
    dataset = Dataset.from_dict(dataset_dict)
    dataset = dataset.map(preprocess_function, batched=False, remove_columns=['comment_id', 'commentary_text', 'trend_label'])
    
    return dataset


def train_model(config_path: str, data_dir: str, output_dir: str = "./outputs"):
    """
    Main training function
    
    Args:
        config_path: Path to configuration YAML file
        data_dir: Path to data directory
        output_dir: Output directory for checkpoints
    """
    # Load configuration
    config = load_config(config_path)
    
    print("=" * 80)
    print("Gold Market Trend Classification - Fine-tuning")
    print("=" * 80)
    
    # Load datasets (JSONL format)
    print("\n[1/5] Loading datasets...")
    data_path = Path(data_dir)
    
    train_samples = []
    val_samples = []
    
    # FAST mode: limit number of samples for quicker runs
    fast_mode = os.environ.get("FAST_MODE", "0") == "1"
    fast_train_samples = int(os.environ.get("FAST_TRAIN_SAMPLES", "800"))
    fast_val_samples = int(os.environ.get("FAST_VAL_SAMPLES", "200"))

    with open(data_path / "train.jsonl", 'r') as f:
        for i, line in enumerate(f):
            if line.strip():
                train_samples.append(json.loads(line))
            if fast_mode and i + 1 >= fast_train_samples:
                break
    
    with open(data_path / "validation.jsonl", 'r') as f:
        for i, line in enumerate(f):
            if line.strip():
                val_samples.append(json.loads(line))
            if fast_mode and i + 1 >= fast_val_samples:
                break
    
    print(f"  Train samples: {len(train_samples)}")
    print(f"  Val samples: {len(val_samples)}")
    
    # Setup model and tokenizer
    print("\n[2/5] Setting up model and tokenizer...")
    model_name = config['model']['base_model']
    model, tokenizer = setup_model_and_tokenizer(model_name, config)
    
    # Setup LoRA
    print("\n[3/5] Configuring LoRA adapters...")
    model = setup_lora(model, config)
    
    # Prepare datasets
    print("\n[4/5] Preparing datasets...")
    train_dataset = convert_dataset_to_hf(train_samples, tokenizer)
    val_dataset = convert_dataset_to_hf(val_samples, tokenizer)
    
    print(f"  Tokenized train samples: {len(train_dataset)}")
    print(f"  Tokenized val samples: {len(val_dataset)}")
    
    # Training arguments
    # If FAST mode, override some training args to speed up and reduce memory
    num_train_epochs = config['training']['num_train_epochs']
    per_device_train_batch_size = config['training']['per_device_train_batch_size']
    per_device_eval_batch_size = config['training']['per_device_eval_batch_size']
    eval_steps = config['training']['eval_steps']
    save_steps = config['training']['save_steps']
    logging_steps = config['training']['logging_steps']

    if fast_mode:
        num_train_epochs = 1
        per_device_train_batch_size = max(1, min(per_device_train_batch_size, 2))
        per_device_eval_batch_size = max(1, min(per_device_eval_batch_size, 2))
        eval_steps = max(50, eval_steps)
        save_steps = 0
        logging_steps = min(logging_steps, 10)

    # Disable mixed precision on CPU/MPS to avoid unsupported autocast
    use_fp16 = config['training']['fp16'] and torch.cuda.is_available()
    use_bf16 = False

    training_args = TrainingArguments(
        output_dir=f"{output_dir}/checkpoint",
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_eval_batch_size,
        gradient_accumulation_steps=config['training']['gradient_accumulation_steps'],
        learning_rate=config['training']['learning_rate'],
        weight_decay=config['training']['weight_decay'],
        warmup_steps=config['training']['warmup_steps'],
        logging_steps=logging_steps,
        eval_steps=eval_steps,
        save_steps=save_steps,
        max_grad_norm=config['training']['max_grad_norm'],
        optim=config['training']['optim'],
        fp16=use_fp16,
        bf16=use_bf16,
        no_cuda=not torch.cuda.is_available(),
        dataloader_num_workers=0,
        dataloader_pin_memory=False,
        report_to=[],
        load_best_model_at_end=config['training']['load_best_model_at_end'],
        metric_for_best_model=config['training']['metric_for_best_model'],
        greater_is_better=config['training']['greater_is_better'],
        eval_strategy="steps",
        save_strategy="steps" if save_steps > 0 else "no",
        run_name=f"gold-trend-{datetime.now().strftime('%Y%m%d_%H%M%S')}{'-FAST' if fast_mode else ''}",
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    # Trainer
    print("\n[5/5] Starting training...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
    )
    
    # Train
    trainer.train()
    
    # Save final model
    final_output_dir = f"{output_dir}/final_model"
    print(f"\nSaving final model to {final_output_dir}...")
    model.save_pretrained(final_output_dir)
    tokenizer.save_pretrained(final_output_dir)
    
    # Save config
    with open(f"{final_output_dir}/training_config.yaml", 'w') as f:
        yaml.dump(config, f)
    
    print("\n" + "=" * 80)
    print("✓ Training completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune LLM for gold trend classification")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--data-dir", type=str, default="data", help="Path to data directory")
    parser.add_argument("--output-dir", type=str, default="outputs", help="Output directory")
    
    args = parser.parse_args()
    # Avoid tokenizers parallelism deadlock warnings after fork
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    # Prefer CPU if CUDA is unavailable to bypass MPS autocast errors
    os.environ.setdefault("ACCELERATE_DISABLE_MPS", "1")
    
    # Ensure wandb stays disabled unless explicitly enabled
    os.environ.setdefault("WANDB_MODE", "offline")
    train_model(args.config, args.data_dir, args.output_dir)
