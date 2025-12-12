"""
Evaluation script for fine-tuned model
"""

import json
import torch
from pathlib import Path
from typing import Dict, List

from scripts.inference import TrendClassifier, EvaluationMetrics


def load_test_data(test_file: str) -> List[Dict]:
    """Load test data from JSONL file"""
    samples = []
    with open(test_file, 'r') as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples


def evaluate_model(model_path: str, test_file: str, output_file: str = None) -> Dict:
    """
    Evaluate fine-tuned model on test set
    
    Args:
        model_path: Path to fine-tuned model
        test_file: Path to test data JSONL file
        output_file: Optional file to save evaluation results
    
    Returns:
        Dictionary with evaluation metrics
    """
    print("="*80)
    print("Evaluating Fine-tuned Model")
    print("="*80)
    
    # Load classifier
    print("\n[1/3] Loading model...")
    classifier = TrendClassifier(model_path)
    
    # Load test data
    print("[2/3] Loading test data...")
    test_samples = load_test_data(test_file)
    print(f"  Test samples: {len(test_samples)}")
    
    # Get predictions
    print("[3/3] Generating predictions...")
    predictions = []
    references = []
    detailed_results = []
    
    for i, sample in enumerate(test_samples):
        commentary = sample['commentary_text']
        reference_trend = sample['trend_label']
        
        result = classifier.classify(commentary)
        predictions.append(result['trend'])
        references.append(reference_trend)
        
        detailed_results.append({
            "comment_id": sample['comment_id'],
            "commentary": commentary,
            "reference_trend": reference_trend,
            "predicted_trend": result['trend'],
            "justification": result['justification'],
            "correct": result['trend'] == reference_trend
        })
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i+1}/{len(test_samples)}")
    
    # Calculate metrics
    print("\nCalculating metrics...")
    metrics = EvaluationMetrics.calculate_metrics(predictions, references)
    
    # Print results
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    print(f"\nAccuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1-Score:  {metrics['f1']:.4f}")
    
    print("\nClassification Report:")
    print(metrics['classification_report'])
    
    # Save results if requested
    if output_file:
        output_data = {
            "metrics": {
                "accuracy": float(metrics['accuracy']),
                "precision": float(metrics['precision']),
                "recall": float(metrics['recall']),
                "f1": float(metrics['f1'])
            },
            "detailed_results": detailed_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\nResults saved to {output_file}")
    
    return metrics


def generate_error_analysis(eval_results_file: str, output_file: str = None):
    """
    Analyze misclassified samples
    
    Args:
        eval_results_file: Path to evaluation results JSON file
        output_file: Optional file to save error analysis
    """
    with open(eval_results_file, 'r') as f:
        results = json.load(f)
    
    errors = [r for r in results['detailed_results'] if not r['correct']]
    
    print("\n" + "="*80)
    print(f"ERROR ANALYSIS ({len(errors)} errors)")
    print("="*80)
    
    # Group errors by type
    error_types = {}
    for error in errors:
        key = f"{error['reference_trend']} -> {error['predicted_trend']}"
        if key not in error_types:
            error_types[key] = []
        error_types[key].append(error)
    
    # Print error summary
    print("\nError Distribution:")
    for error_type, samples in error_types.items():
        print(f"  {error_type}: {len(samples)} errors")
    
    # Print sample errors
    print("\nSample Errors (first 3):")
    for i, error in enumerate(errors[:3]):
        print(f"\n[Error {i+1}]")
        print(f"  Reference: {error['reference_trend']}")
        print(f"  Predicted: {error['predicted_trend']}")
        print(f"  Commentary: {error['commentary'][:100]}...")
        print(f"  Justification: {error['justification']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned model")
    parser.add_argument("--model", type=str, default="outputs/final_model", help="Path to model")
    parser.add_argument("--test-file", type=str, default="data/test.jsonl", help="Path to test file")
    parser.add_argument("--output", type=str, default="evaluation/results.json", help="Output file for results")
    
    args = parser.parse_args()
    
    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Evaluate
    metrics = evaluate_model(args.model, args.test_file, args.output)
    
    # Error analysis
    if Path(args.output).exists():
        generate_error_analysis(args.output)
