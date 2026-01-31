"""
Data loader for the Cambridge DIS Hackathon.

Loads claim/truth pairs from CSV files.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator

from checker_of_facts.hackathon_models import ClaimTruthPair


def load_claim_truth_pairs(csv_path: str | Path) -> list[ClaimTruthPair]:
    """Load claim/truth pairs from a CSV file.
    
    Expected CSV format:
    - Column 1: "claim" - The external claim (tweet, headline, summary)
    - Column 2: "truth" - The internal fact (source truth)
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        List of ClaimTruthPair objects
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    pairs: list[ClaimTruthPair] = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader, 1):
            claim = row.get("claim", "").strip()
            truth = row.get("truth", "").strip()
            
            if claim and truth:
                pairs.append(
                    ClaimTruthPair(
                        claim=claim,
                        truth=truth,
                        pair_id=f"pair_{idx:03d}",
                    )
                )
    
    return pairs


def iter_claim_truth_pairs(csv_path: str | Path) -> Iterator[ClaimTruthPair]:
    """Iterate over claim/truth pairs from a CSV file.
    
    Yields:
        ClaimTruthPair objects one at a time
    """
    for pair in load_claim_truth_pairs(csv_path):
        yield pair


def select_pairs(
    pairs: list[ClaimTruthPair],
    indices: list[int] | None = None,
    count: int | None = None,
) -> list[ClaimTruthPair]:
    """Select a subset of pairs for processing.
    
    Args:
        pairs: Full list of pairs
        indices: Specific indices to select (1-indexed for user convenience)
        count: Number of pairs to select from the start
        
    Returns:
        Selected subset of pairs
    """
    if indices is not None:
        # Convert to 0-indexed and select
        return [pairs[i - 1] for i in indices if 0 < i <= len(pairs)]
    elif count is not None:
        return pairs[:count]
    else:
        return pairs
