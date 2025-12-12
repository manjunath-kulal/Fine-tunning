#!/bin/zsh

# Fast pipeline: smaller model + fewer samples + 1 epoch
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Project directory: $PROJECT_DIR"

export FAST_MODE=1
export FAST_TRAIN_SAMPLES=800
export FAST_VAL_SAMPLES=200

# Optional: use smaller model just for this run by patching env
# To change model permanently, edit config.yaml

printf "\n[Fast Step 1] Generating synthetic dataset (already quick)...\n"
python "$PROJECT_DIR/scripts/generate_synthetic_data.py"
printf "✓ Dataset generated (fast mode will subsample during training)\n\n"

printf "[Fast Step 2] Fine-tuning (1 epoch, small batches, short seq)...\n"
python "$PROJECT_DIR/scripts/fine_tune.py" \
  --config "$PROJECT_DIR/config.yaml" \
  --data-dir "$PROJECT_DIR/data" \
  --output-dir "$PROJECT_DIR/outputs"
printf "✓ Fast fine-tuning completed\n\n"

printf "[Fast Step 3] Evaluating model (on full test set)...\n"
python "$PROJECT_DIR/evaluation/evaluate.py" \
  --model "$PROJECT_DIR/outputs/final_model" \
  --test-file "$PROJECT_DIR/data/test.jsonl" \
  --output "$PROJECT_DIR/evaluation/results_fast.json"
printf "✓ Evaluation completed\n\n"

printf "Results:\n"
printf "  Model: %s\n" "$PROJECT_DIR/outputs/final_model"
printf "  Fast evaluation: %s\n" "$PROJECT_DIR/evaluation/results_fast.json"
