#!/bin/bash

# Gold Market Trend Classification - Fine-tuning Pipeline
# This script orchestrates the entire workflow

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Project directory: $PROJECT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Gold Market Trend Classification${NC}"
echo -e "${BLUE}Fine-tuning Pipeline${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Step 1: Generate synthetic data
echo -e "${YELLOW}[Step 1] Generating synthetic dataset...${NC}"
python "$PROJECT_DIR/scripts/generate_synthetic_data.py"
echo -e "${GREEN}✓ Dataset generated${NC}\n"

# Step 2: Run fine-tuning
echo -e "${YELLOW}[Step 2] Starting model fine-tuning...${NC}"
python "$PROJECT_DIR/scripts/fine_tune.py" \
    --config "$PROJECT_DIR/config.yaml" \
    --data-dir "$PROJECT_DIR/data" \
    --output-dir "$PROJECT_DIR/outputs"
echo -e "${GREEN}✓ Fine-tuning completed${NC}\n"

# Step 3: Run evaluation
echo -e "${YELLOW}[Step 3] Evaluating model...${NC}"
python "$PROJECT_DIR/evaluation/evaluate.py" \
    --model "$PROJECT_DIR/outputs/final_model" \
    --test-file "$PROJECT_DIR/data/test.jsonl" \
    --output "$PROJECT_DIR/evaluation/results.json"
echo -e "${GREEN}✓ Evaluation completed${NC}\n"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Pipeline completed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\nResults:"
echo -e "  Model: $PROJECT_DIR/outputs/final_model"
echo -e "  Evaluation: $PROJECT_DIR/evaluation/results.json"
