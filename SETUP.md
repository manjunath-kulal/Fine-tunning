# SETUP AND EXECUTION GUIDE

## System Requirements

**Operating System:** macOS (current environment)
**Python Version:** 3.8+
**GPU:** NVIDIA (CUDA-enabled) or AMD (ROCm) recommended
**RAM:** 16GB minimum
**Storage:** 30GB free space
**Internet:** Required for model downloads

## Pre-Installation Checklist

```bash
# Check Python version
python --version
# Output should be: Python 3.10+ (or 3.8+)

# Check if pip is installed
pip --version

# Check if CUDA is available (optional)
python -c "import torch; print(torch.cuda.is_available())"
```

## Installation Steps

### 1. Navigate to Project Directory

```bash
cd "/Users/manjunathkulal/Desktop/own project /fine_tunning"
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate
# Output: (venv) user@mac ~/Desktop/own\ project/fine_tunning

# Verify activation
which python
# Should show path containing /venv/
```

### 3. Upgrade pip and Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify installation (takes ~2 minutes)
pip list | grep -E "torch|transformers|peft"
```

### 4. Authenticate with HuggingFace (Required for Model Download)

```bash
# Install HuggingFace CLI
pip install huggingface-hub

# Login to HuggingFace
huggingface-cli login
# Follow prompts to enter your token from https://huggingface.co/settings/tokens

# Verify authentication
huggingface-cli whoami
```

## Quick Start Execution

### Option A: Run Complete Pipeline (Recommended for First Run)

```bash
# Make script executable
chmod +x run_pipeline.sh

# Run the pipeline
bash run_pipeline.sh
```

**What this does:**
1. Generates 5,000 synthetic training samples
2. Trains model with LoRA fine-tuning (2-4 hours)
3. Evaluates on test set
4. Generates classification report

### Option B: Run Individual Steps

#### Step 1: Generate Synthetic Dataset

```bash
python scripts/generate_synthetic_data.py
```

**Output:**
```
Generating synthetic gold market commentary dataset...
Target samples: 5000

Dataset saved to ./data/full_dataset.jsonl
Total samples: 5000

Class Distribution:
      up:  1661 ( 33.2%)
    down:  1677 ( 33.5%)
  sideways:  1662 ( 33.3%)

✓ Dataset generation complete!
  Train set: 4000 samples
  Val set: 500 samples
  Test set: 500 samples
```

**Generated Files:**
- `data/full_dataset.jsonl` - All 5000 samples
- `data/train.jsonl` - 4000 training samples
- `data/validation.jsonl` - 500 validation samples
- `data/test.jsonl` - 500 test samples

#### Step 2: Fine-tune Model

```bash
python scripts/fine_tune.py \
    --config config.yaml \
    --data-dir data \
    --output-dir outputs
```

**Configuration Notes:**
- Modify `config.yaml` to change hyperparameters
- Base model downloads automatically (~15GB)
- First run takes longer due to model download

**Expected Output:**
```
================================================================================
Gold Market Trend Classification - Fine-tuning
================================================================================

[1/5] Loading datasets...
  Train samples: 4000
  Val samples: 500

[2/5] Setting up model and tokenizer...
[3/5] Configuring LoRA adapters...
[4/5] Preparing datasets...
[5/5] Starting training...

Epoch 1/3: [████████████████████] 100%
Epoch 2/3: [████████████████████] 100%
Epoch 3/3: [████████████████████] 100%

Saving final model to ./outputs/final_model...

================================================================================
✓ Training completed successfully!
================================================================================
```

**Generated Files:**
- `outputs/checkpoint/` - Intermediate checkpoints
- `outputs/final_model/` - Final fine-tuned model
- `outputs/final_model/adapter_model.bin` - LoRA weights
- `outputs/final_model/training_config.yaml` - Training config

#### Step 3: Evaluate Model

```bash
python evaluation/evaluate.py \
    --model outputs/final_model \
    --test-file data/test.jsonl \
    --output evaluation/results.json
```

**Expected Output:**
```
================================================================================
Evaluating Fine-tuned Model
================================================================================

[1/3] Loading model...
[2/3] Loading test data...
  Test samples: 500
[3/3] Generating predictions...
  Processed 50/500
  Processed 100/500
  ...

================================================================================
EVALUATION RESULTS
================================================================================

Accuracy:  0.8760
Precision: 0.8720
Recall:    0.8750
F1-Score:  0.8735

Classification Report:
              precision    recall  f1-score   support
         
        down       0.88      0.87      0.87       166
          up       0.86      0.88      0.87       167
     sideways       0.88      0.87      0.87       167

   accuracy                           0.87       500
```

**Generated Files:**
- `evaluation/results.json` - Detailed results

#### Step 4: Run Inference

```bash
python scripts/inference.py
```

**Expected Output:**
```
Model loaded on cuda

================================================================================
Testing Trend Classification
================================================================================

[Sample 1]
Commentary: Gold showing strong bullish momentum with price breaking above...
Trend: UPTREND
Justification: Gold market analysis indicates up trend based on technical...

[Sample 2]
Commentary: Gold breaking below key support levels with increasing selling...
Trend: DOWNTREND
Justification: Gold market analysis indicates down trend based on technical...

[Sample 3]
Commentary: Gold consolidating in a tight range with mixed technical signals...
Trend: SIDEWAYS
Justification: Gold market analysis indicates sideways trend based on...
```

## Manual Testing

### Test Individual Classification

Create a file `test_inference.py`:

```python
from scripts.inference import TrendClassifier

# Initialize classifier
classifier = TrendClassifier("outputs/final_model")

# Test samples
test_cases = [
    "Gold showing strong bullish momentum with price breaking above key resistance levels. Technical indicators confirm uptrend continuation.",
    "Gold breaking below key support levels with increasing selling pressure. Downtrend now confirmed.",
    "Gold consolidating in a tight range with mixed technical signals. No clear directional bias evident."
]

print("Testing Fine-tuned Model:")
print("="*80)

for i, commentary in enumerate(test_cases, 1):
    result = classifier.classify(commentary)
    print(f"\n[Test Case {i}]")
    print(f"Commentary: {commentary[:60]}...")
    print(f"Trend: {result['trend_label'].upper()}")
    print(f"Confidence: {result.get('confidence', 'N/A')}")
    print(f"Justification: {result['justification']}")
```

Run it:
```bash
python test_inference.py
```

## Troubleshooting

### Issue 1: Module Not Found Errors

```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate

# Or install missing package
pip install <package_name>
```

### Issue 2: CUDA Out of Memory

```bash
# Solution: Reduce batch size in config.yaml
# Change: per_device_train_batch_size: 8
# To: per_device_train_batch_size: 4

# Or reduce sequence length
# Change: max_seq_length: 512
# To: max_seq_length: 256
```

### Issue 3: GPU Not Detected

```bash
# Check if CUDA is available
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# If False, install CPU version (slower)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Issue 4: HuggingFace Authentication Failed

```bash
# Re-authenticate
huggingface-cli logout
huggingface-cli login

# Or use token directly
export HF_TOKEN="your_token_here"
```

### Issue 5: Model Download Timeout

```bash
# Download model manually first
huggingface-cli download Qwen/Qwen2-7B-Instruct

# Or use alternative model
# Edit config.yaml: base_model: "meta-llama/Llama-2-7b-chat-hf"
```

## Performance Optimization

### For Faster Training

```yaml
# In config.yaml
training:
  num_train_epochs: 2  # Reduce from 3
  per_device_train_batch_size: 16  # Increase (if memory allows)
  eval_steps: 400  # Evaluate less frequently
```

### For Better Accuracy

```yaml
# In config.yaml
training:
  num_train_epochs: 5  # Train longer
  learning_rate: 1.0e-4  # Lower learning rate
  warmup_steps: 200  # More warmup
```

### For Memory Efficiency

```yaml
# In config.yaml
model:
  max_seq_length: 256  # Shorter sequences
training:
  per_device_train_batch_size: 4  # Smaller batches
  gradient_accumulation_steps: 8  # Accumulate gradients
```

## Monitoring Training

### Option 1: Weights & Biases (Recommended)

```bash
# Install W&B
pip install wandb

# Login
wandb login

# Check dashboard at: https://wandb.ai/your-username/gold-trend
```

### Option 2: TensorBoard

```bash
# Install TensorBoard
pip install tensorboard

# Launch in another terminal
tensorboard --logdir outputs/checkpoint/runs
```

## Next Steps After Training

### 1. Save for Production

```python
# Merge LoRA adapters into base model
from peft import AutoPeftModelForCausalLM

model = AutoPeftModelForCausalLM.from_pretrained("outputs/final_model")
merged_model = model.merge_and_unload()
merged_model.save_pretrained("outputs/merged_model")
```

### 2. Create API Service

```python
# Create FastAPI service (requires: pip install fastapi uvicorn)
from fastapi import FastAPI
from scripts.inference import TrendClassifier

app = FastAPI()
classifier = TrendClassifier("outputs/final_model")

@app.post("/classify")
def classify_trend(commentary: str):
    result = classifier.classify(commentary)
    return result

# Run: uvicorn app:app --reload
```

### 3. Deploy to Cloud

```bash
# Prepare model for deployment
python scripts/inference.py --export-onnx outputs/model.onnx

# Or containerize with Docker
docker build -t gold-trend-classifier .
docker run -p 8000:8000 gold-trend-classifier
```

## Directory Structure After Execution

```
fine_tunning/
├── data/
│   ├── full_dataset.jsonl
│   ├── train.jsonl
│   ├── validation.jsonl
│   └── test.jsonl
│
├── outputs/
│   ├── checkpoint/
│   │   ├── runs/
│   │   └── ...checkpoints...
│   └── final_model/
│       ├── adapter_model.bin
│       ├── adapter_config.json
│       ├── config.json
│       ├── generation_config.json
│       ├── pytorch_model.bin
│       ├── special_tokens_map.json
│       ├── tokenizer.json
│       ├── tokenizer.model
│       ├── tokenizer_config.json
│       ├── training_config.yaml
│       └── training_args.bin
│
├── evaluation/
│   └── results.json
│
└── [other files...]
```

## Verification Checklist

After completing all steps:

- [ ] Virtual environment activated
- [ ] Dependencies installed successfully
- [ ] Synthetic dataset generated (5000 samples)
- [ ] Model fine-tuned successfully
- [ ] Evaluation completed (accuracy > 80%)
- [ ] Inference working on test samples
- [ ] Model can be loaded for predictions

## Support & Resources

- **Documentation:** See README.md
- **Config Reference:** See config.yaml with comments
- **HuggingFace Hub:** https://huggingface.co
- **PEFT Documentation:** https://huggingface.co/docs/peft
- **Qwen Model:** https://huggingface.co/Qwen

## Estimated Timing

| Step | Time | Notes |
|------|------|-------|
| Setup | 10 min | Installing dependencies |
| Data Generation | 2 min | Generating 5000 samples |
| Model Download | 10-15 min | First time only (~15GB) |
| Fine-tuning | 2-4 hours | Depends on GPU (3 epochs) |
| Evaluation | 5 min | Testing on 500 samples |
| **Total** | **2.5-4.5 hours** | Mostly waiting for training |

---

**Ready to start?** Run: `bash run_pipeline.sh`

---

Last Updated: December 11, 2025
