# Gold Market Trend Classification - Fine-tuning Project

A comprehensive solution for fine-tuning LLMs (Qwen/LLaMA) to classify gold market trends from analyst commentary.

## Project Overview

**Problem:** Classify gold market trend direction (Uptrend/Downtrend/Sideways) from short analyst commentary text.

**Solution:** Fine-tune a large language model using LoRA (Low-Rank Adaptation) with synthetic training data to:
- Accurately classify trend direction
- Generate technical justifications
- Support trading automation

## Dataset

- **Size:** 5,000 synthetic samples
- **Source:** Synthetically generated with realistic market terminology
- **Structure:** 
  - `comment_id`: Unique identifier
  - `commentary_text`: Analyst/trader commentary
  - `trend_label`: up / down / sideways
- **Split:** 80% train / 10% validation / 10% test

## Project Structure

```
fine_tunning/
├── data/                          # Dataset directory
│   ├── full_dataset.jsonl        # Complete dataset
│   ├── train.jsonl               # Training split (4000 samples)
│   ├── validation.jsonl          # Validation split (500 samples)
│   └── test.jsonl                # Test split (500 samples)
│
├── scripts/                       # Core scripts
│   ├── generate_synthetic_data.py # Dataset generation
│   ├── data_preparation.py        # Data loading and preprocessing
│   ├── fine_tune.py               # LoRA fine-tuning training loop
│   └── inference.py               # Inference and evaluation metrics
│
├── evaluation/                    # Evaluation modules
│   ├── evaluate.py                # Model evaluation script
│   └── results.json               # Evaluation results (generated)
│
├── outputs/                       # Fine-tuned models
│   ├── checkpoint/                # Training checkpoints
│   └── final_model/               # Final fine-tuned model
│
├── models/                        # Reference models directory
├── config.yaml                    # Configuration file
├── requirements.txt               # Python dependencies
├── run_pipeline.sh                # Complete pipeline script
└── README.md                      # This file
```

## Installation

1. **Clone/Setup Project**
```bash
cd /Users/manjunathkulal/Desktop/own\ project/fine_tunning
```

2. **Create Virtual Environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

## Quick Start

### Option 1: Run Complete Pipeline (Recommended)
```bash
bash run_pipeline.sh
```

This executes all steps:
1. Generate synthetic dataset
2. Fine-tune model
3. Evaluate on test set

### Option 2: Run Individual Steps

**Step 1: Generate Dataset**
```bash
python scripts/generate_synthetic_data.py
```

**Step 2: Fine-tune Model**
```bash
python scripts/fine_tune.py \
    --config config.yaml \
    --data-dir data \
    --output-dir outputs
```

**Step 3: Evaluate Model**
```bash
python evaluation/evaluate.py \
    --model outputs/final_model \
    --test-file data/test.jsonl \
    --output evaluation/results.json
```

**Step 4: Run Inference**
```bash
python scripts/inference.py
```

## Configuration

Edit `config.yaml` to customize:

```yaml
# Model selection
model:
  base_model: "Qwen/Qwen2-7B-Instruct"  # or "meta-llama/Llama-2-7b-chat-hf"
  max_seq_length: 512

# LoRA parameters
lora:
  r: 16
  lora_alpha: 32
  lora_dropout: 0.05

# Training hyperparameters
training:
  num_train_epochs: 3
  per_device_train_batch_size: 8
  learning_rate: 2.0e-4
  # ... more options
```

## Usage Examples

### Classification with Fine-tuned Model

```python
from scripts.inference import TrendClassifier

# Load fine-tuned model
classifier = TrendClassifier("outputs/final_model")

# Classify commentary
commentary = "Gold showing strong bullish momentum with price breaking above key resistance levels."
result = classifier.classify(commentary)

print(f"Trend: {result['trend_label']}")  # OUTPUT: uptrend
print(f"Justification: {result['justification']}")
```

### Batch Processing

```python
commentaries = [
    "Gold breaking below key support with selling pressure...",
    "Consolidating in range with mixed signals...",
    # ... more commentaries
]

results = classifier.batch_classify(commentaries, batch_size=4)
```

### Evaluation

```python
from evaluation.evaluate import evaluate_model

metrics = evaluate_model(
    model_path="outputs/final_model",
    test_file="data/test.jsonl",
    output_file="evaluation/results.json"
)

print(f"Accuracy: {metrics['accuracy']:.4f}")
print(f"F1-Score: {metrics['f1']:.4f}")
```

## Model Architecture

### Base Models Supported
- **Qwen2-7B-Instruct** (Recommended for efficiency)
- **LLaMA-2-7B-Chat** (Alternative option)

### Fine-tuning Approach: LoRA (Low-Rank Adaptation)

**Benefits:**
- 🚀 **Efficient:** Only ~1-3% of base model parameters trainable
- ⚡ **Fast:** Trains in hours instead of days
- 💾 **Compact:** Adapter weights ~100MB vs full model 14GB+
- 💰 **Cost-effective:** Runs on consumer GPUs (8GB VRAM)

**Architecture:**
```
Frozen Base Model (7B params)
         ↓
    [LoRA Adapters]  ← Only these are trained
         ↓
   Fine-tuned Output
```

## Expected Performance

After fine-tuning on 5,000 samples:

| Metric | Expected | Details |
|--------|----------|---------|
| Accuracy | 85-90% | Overall correct classifications |
| Precision | 83-88% | Per-class accuracy |
| Recall | 82-87% | Coverage of each class |
| F1-Score | 84-88% | Balanced performance |

*Actual results depend on data quality and hyperparameters*

## Training Details

### Hardware Requirements
- **GPU:** 8GB VRAM minimum (NVIDIA or compatible)
- **RAM:** 16GB system memory
- **Storage:** ~30GB (models + data)
- **Time:** 2-4 hours for 3 epochs (depends on hardware)

### Optimization Techniques
1. **4-bit Quantization:** Reduces memory footprint
2. **Flash Attention:** Faster attention computation
3. **Gradient Accumulation:** Effective larger batch sizes
4. **Mixed Precision (FP16):** Speed and memory optimization

### Training Hyperparameters
```yaml
- Learning Rate: 2.0e-4 (LoRA-optimized)
- Batch Size: 8 (per device)
- Gradient Accumulation: 4 steps
- Warmup Steps: 100
- Epochs: 3
- Max Grad Norm: 1.0
```

## Output Files

### Model Files
- `outputs/final_model/` - Fine-tuned model weights
- `outputs/final_model/adapter_config.json` - LoRA configuration
- `outputs/final_model/adapter_model.bin` - LoRA weights (~100MB)

### Training Logs
- `outputs/checkpoint/` - Intermediate checkpoints
- Training metrics logged to Weights & Biases (optional)

### Evaluation Results
- `evaluation/results.json` - Detailed metrics and predictions
  ```json
  {
    "metrics": {
      "accuracy": 0.876,
      "precision": 0.872,
      "recall": 0.875,
      "f1": 0.873
    },
    "detailed_results": [...]
  }
  ```

## Inference Output Format

```python
{
    "trend": "up",                          # Raw trend label
    "trend_label": "uptrend",               # Formatted label
    "justification": "Gold showing strong...", # Technical explanation
    "raw_response": "TREND: up\n..."        # Full model output
}
```

## Troubleshooting

### Out of Memory (OOM) Errors
```bash
# Reduce batch size in config.yaml
per_device_train_batch_size: 4  # Instead of 8

# Or reduce sequence length
max_seq_length: 256  # Instead of 512
```

### GPU Not Detected
```bash
python -c "import torch; print(torch.cuda.is_available())"
# Should print: True
```

### Model Download Issues
```bash
# Pre-download model
huggingface-cli download Qwen/Qwen2-7B-Instruct
```

## Advanced Usage

### Custom Prompt Templates

Edit the `SYSTEM_PROMPT` in `scripts/data_preparation.py`:

```python
SYSTEM_PROMPT = """Your custom system message here..."""
```

### Adding More Training Data

Add samples to `data/train.jsonl` in format:
```json
{"comment_id": "ID_00000", "commentary_text": "...", "trend_label": "up"}
```

### Model Merging

Merge LoRA adapters into base model:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2-7B-Instruct")
model = PeftModel.from_pretrained(base_model, "outputs/final_model")
merged = model.merge_and_unload()
merged.save_pretrained("merged_model")
```

## Results & Monitoring

### Training Metrics
- Loss curves logged during training
- Validation metrics evaluated every 200 steps
- Best model saved based on validation accuracy

### Evaluation Metrics
- Per-class precision, recall, F1
- Confusion matrix analysis
- Error case identification

### Weights & Biases Integration
```bash
# Enable W&B logging (automatic in training script)
wandb login  # Enter your API key
```

## References

- [PEFT Library Documentation](https://huggingface.co/docs/peft)
- [Qwen Model Card](https://huggingface.co/Qwen/Qwen2-7B-Instruct)
- [LoRA Paper: Low-Rank Adaptation](https://arxiv.org/abs/2106.09685)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)

## Next Steps

1. **Optimize Prompts:** Refine system/user prompts for better performance
2. **Data Augmentation:** Add real market commentary samples
3. **Model Merging:** Merge adapters for deployment
4. **API Integration:** Wrap model in FastAPI/Flask service
5. **A/B Testing:** Compare with baseline models

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review HuggingFace documentation
3. Check error logs in `outputs/` directory

---

**Last Updated:** December 11, 2025

**Status:** Ready for Production
