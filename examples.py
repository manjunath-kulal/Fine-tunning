"""
Example usage patterns for the gold trend classification system
"""

# Example 1: Basic Classification
# ================================

from scripts.inference import TrendClassifier

# Initialize the classifier
classifier = TrendClassifier(model_path="outputs/final_model")

# Single classification
commentary = "Gold showing strong bullish momentum with price breaking above key resistance levels."
result = classifier.classify(commentary)

print(f"Trend: {result['trend_label']}")
print(f"Justification: {result['justification']}")


# Example 2: Batch Processing
# ============================

commentaries = [
    "Gold showing strong bullish momentum with price breaking above key resistance levels. Technical indicators confirm uptrend continuation.",
    "Gold breaking below key support levels with increasing selling pressure. Downtrend now confirmed.",
    "Gold consolidating in a tight range with mixed technical signals. No clear directional bias evident.",
]

results = classifier.batch_classify(commentaries)

for i, result in enumerate(results, 1):
    print(f"\n[Sample {i}]")
    print(f"Trend: {result['trend_label']}")
    print(f"Justification: {result['justification']}")


# Example 3: Evaluation Metrics
# ==============================

from evaluation.evaluate import evaluate_model
import json

# Evaluate on test set
metrics = evaluate_model(
    model_path="outputs/final_model",
    test_file="data/test.jsonl",
    output_file="evaluation/results.json"
)

print(f"Accuracy: {metrics['accuracy']:.4f}")
print(f"F1-Score: {metrics['f1']:.4f}")

# Load detailed results
with open("evaluation/results.json", 'r') as f:
    results = json.load(f)
    
for result in results['detailed_results'][:5]:
    print(f"\n{result['comment_id']}")
    print(f"  Reference: {result['reference_trend']}")
    print(f"  Predicted: {result['predicted_trend']}")
    print(f"  Correct: {result['correct']}")


# Example 4: Custom Model Loading
# ================================

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import AutoPeftModelForCausalLM

# Load fine-tuned model with LoRA adapters
model = AutoPeftModelForCausalLM.from_pretrained(
    "outputs/final_model",
    device_map="auto",
    torch_dtype=torch.float16
)

tokenizer = AutoTokenizer.from_pretrained("outputs/final_model")

# Generate prediction
input_text = "Gold showing strong bullish momentum..."
inputs = tokenizer(input_text, return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=50)
    
prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(prediction)


# Example 5: Model Merging for Production
# ========================================

from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2-7B-Instruct")

# Load with LoRA adapters
lora_model = PeftModel.from_pretrained(base_model, "outputs/final_model")

# Merge adapters into base model
merged_model = lora_model.merge_and_unload()

# Save merged model
merged_model.save_pretrained("outputs/merged_model")
tokenizer.save_pretrained("outputs/merged_model")

print("Model merged and saved to outputs/merged_model")


# Example 6: Custom Inference with Confidence
# ============================================

class ConfidenceClassifier:
    def __init__(self, model_path):
        self.classifier = TrendClassifier(model_path)
    
    def classify_with_confidence(self, commentary, num_samples=5):
        """Estimate confidence by running multiple samples with temperature sampling"""
        predictions = {}
        
        for _ in range(num_samples):
            result = self.classifier.classify(commentary, temperature=0.8)
            trend = result['trend']
            predictions[trend] = predictions.get(trend, 0) + 1
        
        # Calculate confidence
        max_votes = max(predictions.values())
        confidence = max_votes / num_samples
        predicted_trend = max(predictions, key=predictions.get)
        
        return {
            "trend": predicted_trend,
            "confidence": confidence,
            "votes": predictions,
            "raw_result": result
        }

# Usage
confidence_classifier = ConfidenceClassifier("outputs/final_model")
result = confidence_classifier.classify_with_confidence(
    "Gold showing mixed signals in consolidation..."
)

print(f"Trend: {result['trend']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Votes: {result['votes']}")


# Example 7: Analysis Pipeline
# =============================

import pandas as pd
from datetime import datetime

class TrendAnalyzer:
    """Analyze multiple commentaries and generate summary"""
    
    def __init__(self, model_path):
        self.classifier = TrendClassifier(model_path)
    
    def analyze_commentaries(self, commentaries_list):
        """Analyze list of commentaries and generate report"""
        results = []
        
        for i, commentary in enumerate(commentaries_list):
            result = self.classifier.classify(commentary)
            results.append({
                'id': i,
                'commentary': commentary,
                'trend': result['trend_label'],
                'justification': result['justification'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(results)
        
        # Summary statistics
        trend_distribution = df['trend'].value_counts()
        
        return {
            'dataframe': df,
            'trend_distribution': trend_distribution,
            'majority_trend': trend_distribution.index[0],
            'consensus': trend_distribution.max() / len(df)
        }

# Usage
analyzer = TrendAnalyzer("outputs/final_model")
commentaries = [
    "Bullish momentum confirmed...",
    "Bearish pressure intensifying...",
    "Range-bound consolidation...",
    "Uptrend intact...",
]

analysis = analyzer.analyze_commentaries(commentaries)
print(f"Majority Trend: {analysis['majority_trend']}")
print(f"Consensus: {analysis['consensus']:.2%}")
print(f"\nTrend Distribution:\n{analysis['trend_distribution']}")


# Example 8: Error Analysis
# ==========================

def analyze_errors(results_file):
    """Analyze misclassified samples"""
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    errors = [r for r in data['detailed_results'] if not r['correct']]
    
    # Group by error type
    error_types = {}
    for error in errors:
        key = f"{error['reference_trend']} -> {error['predicted_trend']}"
        if key not in error_types:
            error_types[key] = []
        error_types[key].append(error)
    
    print("Error Analysis:")
    print(f"Total Errors: {len(errors)}")
    print("\nError Distribution:")
    for error_type, samples in error_types.items():
        print(f"  {error_type}: {len(samples)} errors")
    
    # Show challenging samples
    print("\nMost Challenging Samples:")
    for i, error in enumerate(errors[:3], 1):
        print(f"\n[Error {i}]")
        print(f"Commentary: {error['commentary'][:100]}...")
        print(f"Expected: {error['reference_trend']}")
        print(f"Got: {error['predicted_trend']}")

# Usage
if __name__ == "__main__":
    analyze_errors("evaluation/results.json")


# Example 9: Real-time Streaming Classification
# ==============================================

import queue
import threading
from collections import deque

class RealTimeClassifier:
    """Process streaming commentaries in real-time"""
    
    def __init__(self, model_path, window_size=10):
        self.classifier = TrendClassifier(model_path)
        self.input_queue = queue.Queue()
        self.results = deque(maxlen=window_size)
    
    def add_commentary(self, commentary):
        """Add commentary to queue for processing"""
        self.input_queue.put(commentary)
    
    def process(self):
        """Process commentaries from queue"""
        while True:
            try:
                commentary = self.input_queue.get(timeout=1)
                if commentary is None:
                    break
                
                result = self.classifier.classify(commentary)
                self.results.append(result)
                
            except queue.Empty:
                continue
    
    def get_trend_summary(self):
        """Get trend summary from recent predictions"""
        if not self.results:
            return None
        
        trend_counts = {}
        for result in self.results:
            trend = result['trend']
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        
        dominant_trend = max(trend_counts, key=trend_counts.get)
        confidence = trend_counts[dominant_trend] / len(self.results)
        
        return {
            'dominant_trend': dominant_trend,
            'confidence': confidence,
            'distribution': trend_counts
        }


# Example 10: Configuration and Logging
# ======================================

import logging
from pathlib import Path

def setup_logging():
    """Setup logging for inference operations"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "inference.log"),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

def classify_with_logging(classifier, commentary):
    """Classify with logging"""
    try:
        logger.info(f"Classifying: {commentary[:50]}...")
        result = classifier.classify(commentary)
        logger.info(f"Result: {result['trend_label']}")
        return result
    except Exception as e:
        logger.error(f"Classification failed: {str(e)}", exc_info=True)
        return None


if __name__ == "__main__":
    print("✓ All examples ready to use!")
    print("\nRun individual examples as needed:")
    print("  python examples.py  # (modify __main__ section)")
