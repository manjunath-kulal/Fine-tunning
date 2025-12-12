"""
Inference module for trend classification
"""

import torch
import json
from pathlib import Path
from typing import Dict, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import AutoPeftModelForCausalLM


class TrendClassifier:
    """Trend classification inference engine"""
    
    TREND_MAPPING = {
        "up": "uptrend",
        "down": "downtrend",
        "sideways": "sideways"
    }
    
    def __init__(self, model_path: str, device: str = "auto"):
        """
        Initialize classifier
        
        Args:
            model_path: Path to fine-tuned model
            device: Device to use (cuda, cpu, or auto)
        """
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load model and tokenizer
        try:
            self.model = AutoPeftModelForCausalLM.from_pretrained(
                model_path,
                device_map=self.device,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
        except:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map=self.device,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model.eval()
        print(f"Model loaded on {self.device}")
    
    def prepare_prompt(self, commentary: str) -> str:
        """Prepare input prompt"""
        prompt = f"""<|im_start|>system
You are an expert gold market analyst. Analyze the given market commentary and classify the trend direction.
Respond with ONLY the trend classification in this format:
TREND: [uptrend/downtrend/sideways]
JUSTIFICATION: [Brief technical justification]<|im_end|>
<|im_start|>user
Market Commentary: {commentary}<|im_end|>
<|im_start|>assistant
"""
        return prompt
    
    def classify(self, commentary: str, temperature: float = 0.7, max_tokens: int = 50) -> Dict:
        """
        Classify trend from commentary
        
        Args:
            commentary: Market commentary text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Dictionary with trend, confidence, and justification
        """
        prompt = self.prepare_prompt(commentary)
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract trend and justification
        trend, justification = self._parse_response(response)
        
        return {
            "trend": trend,
            "trend_label": self.TREND_MAPPING.get(trend, "unknown"),
            "justification": justification,
            "raw_response": response
        }
    
    @staticmethod
    def _parse_response(response: str) -> Tuple[str, str]:
        """
        Parse model response to extract trend and justification
        
        Args:
            response: Raw model response
        
        Returns:
            Tuple of (trend, justification)
        """
        trend = "sideways"
        justification = "Unable to determine clear trend direction"
        
        lines = response.split('\n')
        for line in lines:
            if "TREND:" in line:
                trend_text = line.replace("TREND:", "").strip().lower()
                if "up" in trend_text:
                    trend = "up"
                elif "down" in trend_text:
                    trend = "down"
                elif "sideways" in trend_text or "neutral" in trend_text:
                    trend = "sideways"
            
            if "JUSTIFICATION:" in line:
                justification = line.replace("JUSTIFICATION:", "").strip()
        
        return trend, justification
    
    def batch_classify(self, commentaries: list, batch_size: int = 4) -> list:
        """
        Classify multiple commentaries
        
        Args:
            commentaries: List of commentary texts
            batch_size: Batch processing size
        
        Returns:
            List of classification results
        """
        results = []
        for i in range(0, len(commentaries), batch_size):
            batch = commentaries[i:i+batch_size]
            for commentary in batch:
                result = self.classify(commentary)
                results.append(result)
        
        return results


class EvaluationMetrics:
    """Calculate evaluation metrics"""
    
    @staticmethod
    def calculate_metrics(predictions: list, references: list) -> Dict:
        """
        Calculate precision, recall, F1 for trend classification
        
        Args:
            predictions: List of predicted trends
            references: List of reference trends
        
        Returns:
            Dictionary of metrics
        """
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
        
        metrics = {
            "accuracy": accuracy_score(references, predictions),
            "precision": precision_score(references, predictions, average='weighted', zero_division=0),
            "recall": recall_score(references, predictions, average='weighted', zero_division=0),
            "f1": f1_score(references, predictions, average='weighted', zero_division=0),
            "classification_report": classification_report(references, predictions, zero_division=0)
        }
        
        return metrics


if __name__ == "__main__":
    # Example usage
    model_path = "./outputs/final_model"
    
    if Path(model_path).exists():
        classifier = TrendClassifier(model_path)
        
        # Test samples
        test_commentaries = [
            "Gold showing strong bullish momentum with price breaking above key resistance levels. Technical indicators confirm uptrend continuation.",
            "Gold breaking below key support levels with increasing selling pressure. Downtrend now confirmed.",
            "Gold consolidating in a tight range with mixed technical signals. No clear directional bias evident."
        ]
        
        print("\n" + "="*80)
        print("Testing Trend Classification")
        print("="*80)
        
        for i, commentary in enumerate(test_commentaries, 1):
            print(f"\n[Sample {i}]")
            print(f"Commentary: {commentary[:80]}...")
            result = classifier.classify(commentary)
            print(f"Trend: {result['trend_label'].upper()}")
            print(f"Justification: {result['justification']}")
    else:
        print(f"Model not found at {model_path}")
        print("Please run fine-tuning first with: python scripts/fine_tune.py")
