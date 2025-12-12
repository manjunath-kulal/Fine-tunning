"""
Generate synthetic gold market commentary dataset
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Uptrend indicators and phrases
UPTREND_INDICATORS = [
    "bullish momentum building",
    "strong resistance breakout",
    "technical buy signals emerging",
    "continuing higher",
    "upward trend intact",
    "buyers in control",
    "higher lows pattern",
    "support holding well",
    "momentum positive",
    "technical strength evident",
    "bull flag formation",
    "golden cross visible",
    "volume supporting rally",
    "sentiment turning positive",
    "consolidation breakout potential",
]

UPTREND_COMMENTS = [
    "Gold showing strong bullish momentum with price breaking above key resistance levels. Technical indicators confirm uptrend continuation.",
    "Buyers maintaining control as gold climbs higher on safe-haven demand. Moving averages aligned bullishly.",
    "Technical analysis supports further gains. Higher lows pattern intact with RSI showing room to run.",
    "USD weakness and geopolitical tensions driving gold higher. Uptrend well established on daily chart.",
    "Recent breakout from consolidation range signals fresh buying interest. Trend followers adding to positions.",
    "Strong support at 1950 level holds well. Every dip being bought. Uptrend trajectory intact.",
    "Technical indicators flashing green. Volume supporting higher prices. Momentum remains positive.",
    "Gold bouncing off support with rising moving averages. Clear uptrend structure on charts.",
    "Institutional buyers accumulating on weakness. Long-term uptrend remains intact despite minor pullbacks.",
    "Fed uncertainty supporting safe-haven flows into gold. Technical picture remains constructive.",
]

# Downtrend indicators and phrases
DOWNTREND_INDICATORS = [
    "bearish breakdown",
    "resistance holding firm",
    "selling pressure mounting",
    "lower highs pattern",
    "downtrend confirmed",
    "bears in control",
    "support breaking down",
    "negative momentum",
    "technical weakness",
    "death cross pattern",
    "selling continues",
    "weakness accelerating",
    "volume selling",
    "sentiment deteriorating",
    "breakdown reversal",
]

DOWNTREND_COMMENTS = [
    "Gold breaking below key support levels with increasing selling pressure. Downtrend now confirmed.",
    "Technical analysis shows weakness. Lower highs and lower lows pattern emerging on daily charts.",
    "Sellers in control as gold extends losses below 1900 level. Bearish momentum intensifying.",
    "Strong dollar and rising yields pressure gold lower. Downtrend appears intact with little support.",
    "Technical breakdown from consolidation range triggered stop losses. Momentum turned negative.",
    "Support levels failing to hold. Bears taking control with accelerating selling activity.",
    "Death cross on weekly chart signals significant weakness ahead. Downtrend firmly established.",
    "Negative technical indicators pointing to further downside. Volume confirming selling interest.",
    "Major support broken. Downtrend trajectory likely to continue. Risk positioned to downside.",
    "Institutional liquidation evident as gold plummets. Technicals deteriorating rapidly.",
]

# Sideways indicators and phrases
SIDEWAYS_INDICATORS = [
    "consolidating",
    "range-bound",
    "equilibrium",
    "indecision",
    "mixed signals",
    "no clear direction",
    "neutral bias",
    "choppy trading",
    "technical indecision",
    "flat momentum",
    "sideways churn",
    "balance of power",
    "stalled move",
    "lacking conviction",
    "trendless market",
]

SIDEWAYS_COMMENTS = [
    "Gold consolidating in a tight range with mixed technical signals. No clear directional bias evident.",
    "Indecision in the market as gold chops sideways between support and resistance. Traders awaiting catalysts.",
    "Technical picture remains neutral with price stuck in equilibrium. No trend conviction on daily chart.",
    "Sideways movement continuing as bulls and bears find balance. Volume declining during consolidation.",
    "Range-bound trading pattern holding. Breakout required in either direction to establish new trend.",
    "Choppy price action with no clear momentum. Indicators giving mixed signals on short-term direction.",
    "Gold lacking conviction and trending nowhere. Safe bet to stay on sidelines until breakout.",
    "Consolidation phase continuing after recent volatility. Technical picture neutral currently.",
    "Trendless market with price oscillating between 1920-1960 range. Breakout imminent likely.",
    "Mixed technical indicators suggest market indecision. Trading range-bound until new catalyst emerges.",
]

def generate_comment_id():
    """Generate unique comment ID"""
    counter = 0
    while True:
        yield f"COMMENT_{counter:05d}"
        counter += 1

def generate_synthetic_data(num_samples: int = 5000, seed: int = 42) -> list:
    """
    Generate synthetic gold market commentary dataset
    
    Args:
        num_samples: Total number of samples to generate
        seed: Random seed for reproducibility
    
    Returns:
        List of dictionaries containing comment_id, commentary_text, and trend_label
    """
    random.seed(seed)
    dataset = []
    comment_id_gen = generate_comment_id()
    
    # Distribute samples across trend classes
    samples_per_trend = num_samples // 3
    
    # Generate uptrend samples
    for _ in range(samples_per_trend):
        comment = random.choice(UPTREND_COMMENTS)
        # Add variation to comments
        if random.random() > 0.7:
            indicators = random.sample(UPTREND_INDICATORS, random.randint(1, 3))
            comment += " " + ", ".join(indicators) + "."
        
        dataset.append({
            "comment_id": next(comment_id_gen),
            "commentary_text": comment,
            "trend_label": "up"
        })
    
    # Generate downtrend samples
    for _ in range(samples_per_trend):
        comment = random.choice(DOWNTREND_COMMENTS)
        if random.random() > 0.7:
            indicators = random.sample(DOWNTREND_INDICATORS, random.randint(1, 3))
            comment += " " + ", ".join(indicators) + "."
        
        dataset.append({
            "comment_id": next(comment_id_gen),
            "commentary_text": comment,
            "trend_label": "down"
        })
    
    # Generate sideways samples
    remaining = num_samples - 2 * samples_per_trend
    for _ in range(remaining):
        comment = random.choice(SIDEWAYS_COMMENTS)
        if random.random() > 0.7:
            indicators = random.sample(SIDEWAYS_INDICATORS, random.randint(1, 3))
            comment += " " + ", ".join(indicators) + "."
        
        dataset.append({
            "comment_id": next(comment_id_gen),
            "commentary_text": comment,
            "trend_label": "sideways"
        })
    
    # Shuffle the dataset
    random.shuffle(dataset)
    
    return dataset

def save_dataset(dataset: list, output_path: str):
    """Save dataset to JSONL format"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for sample in dataset:
            f.write(json.dumps(sample) + '\n')
    
    print(f"Dataset saved to {output_path}")
    print(f"Total samples: {len(dataset)}")
    
    # Print class distribution
    trends = {}
    for sample in dataset:
        trend = sample['trend_label']
        trends[trend] = trends.get(trend, 0) + 1
    
    print("\nClass Distribution:")
    for trend, count in sorted(trends.items()):
        percentage = (count / len(dataset)) * 100
        print(f"  {trend:12s}: {count:4d} ({percentage:5.1f}%)")

def create_train_val_test_split(dataset: list, 
                               train_ratio: float = 0.8,
                               val_ratio: float = 0.1,
                               test_ratio: float = 0.1,
                               seed: int = 42) -> tuple:
    """Split dataset into train, val, test sets"""
    random.seed(seed)
    random.shuffle(dataset)
    
    n = len(dataset)
    train_size = int(n * train_ratio)
    val_size = int(n * val_ratio)
    
    train_set = dataset[:train_size]
    val_set = dataset[train_size:train_size + val_size]
    test_set = dataset[train_size + val_size:]
    
    return train_set, val_set, test_set

if __name__ == "__main__":
    # Configuration
    NUM_SAMPLES = 5000
    SEED = 42
    DATA_DIR = Path(__file__).parent.parent / "data"
    
    print("Generating synthetic gold market commentary dataset...")
    print(f"Target samples: {NUM_SAMPLES}")
    print()
    
    # Generate full dataset
    full_dataset = generate_synthetic_data(NUM_SAMPLES, SEED)
    
    # Save full dataset
    full_path = DATA_DIR / "full_dataset.jsonl"
    save_dataset(full_dataset, str(full_path))
    
    # Create splits
    train_set, val_set, test_set = create_train_val_test_split(
        full_dataset, 
        train_ratio=0.8,
        val_ratio=0.1,
        test_ratio=0.1,
        seed=SEED
    )
    
    # Save splits
    save_dataset(train_set, str(DATA_DIR / "train.jsonl"))
    save_dataset(val_set, str(DATA_DIR / "validation.jsonl"))
    save_dataset(test_set, str(DATA_DIR / "test.jsonl"))
    
    print("\n✓ Dataset generation complete!")
    print(f"  Train set: {len(train_set)} samples")
    print(f"  Val set: {len(val_set)} samples")
    print(f"  Test set: {len(test_set)} samples")
