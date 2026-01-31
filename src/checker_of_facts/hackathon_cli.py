#!/usr/bin/env python3
"""
CLI for the Cambridge DIS Hackathon Jury Debate System.

Usage:
    # Run debate on a single claim/truth pair from command line
    python -m checker_of_facts.hackathon_cli --claim "..." --truth "..."
    
    # Run debate on pairs from CSV file
    python -m checker_of_facts.hackathon_cli --csv path/to/data.csv --count 5
    
    # Run specific pairs by index
    python -m checker_of_facts.hackathon_cli --csv path/to/data.csv --indices 1 3 5
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from checker_of_facts.data_loader import load_claim_truth_pairs, select_pairs
from checker_of_facts.hackathon_engine import HackathonDebateEngine
from checker_of_facts.hackathon_models import ClaimTruthPair, DebateResult


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Cambridge DIS Hackathon: Multi-Agent Jury Debate for Fact Checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Debate a single pair
  python -m checker_of_facts.hackathon_cli \\
      --claim "Germany had less than 13,200 cases..." \\
      --truth "As of 19 March 2020, Germany has reported 13,083 cases..."

  # Load from CSV (first 5 pairs)
  python -m checker_of_facts.hackathon_cli --csv Polaris.csv --count 5

  # Load specific pairs by index
  python -m checker_of_facts.hackathon_cli --csv Polaris.csv --indices 1 3 7
        """,
    )
    
    # Input source options
    input_group = parser.add_argument_group("Input Options")
    input_group.add_argument(
        "--claim",
        type=str,
        help="External claim text (use with --truth)",
    )
    input_group.add_argument(
        "--truth",
        type=str,
        help="Internal fact / ground truth (use with --claim)",
    )
    input_group.add_argument(
        "--csv",
        type=Path,
        help="Path to CSV file with claim/truth pairs",
    )
    input_group.add_argument(
        "--count",
        type=int,
        help="Number of pairs to process from CSV (from start)",
    )
    input_group.add_argument(
        "--indices",
        type=int,
        nargs="+",
        help="Specific pair indices to process (1-indexed)",
    )
    
    # Model options
    model_group = parser.add_argument_group("Model Options")
    model_group.add_argument(
        "--model",
        type=str,
        default="gpt-4.1-mini",
        help="OpenAI model to use (default: gpt-4.1-mini)",
    )
    model_group.add_argument(
        "--premium",
        action="store_true",
        help="Use premium model (gpt-4o) for demo",
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress real-time output (only show final JSON)",
    )
    output_group.add_argument(
        "--output",
        type=Path,
        help="Save results to JSON file",
    )
    
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    has_manual = args.claim is not None or args.truth is not None
    has_csv = args.csv is not None
    
    if has_manual and has_csv:
        raise ValueError("Cannot use both --claim/--truth and --csv. Choose one input method.")
    
    if not has_manual and not has_csv:
        raise ValueError("Must specify either --claim and --truth, or --csv.")
    
    if has_manual:
        if args.claim is None or args.truth is None:
            raise ValueError("Both --claim and --truth must be provided together.")
    
    if has_csv and not args.csv.exists():
        raise ValueError(f"CSV file not found: {args.csv}")


def get_pairs_to_process(args: argparse.Namespace) -> list[ClaimTruthPair]:
    """Get the claim/truth pairs to process based on arguments."""
    if args.claim and args.truth:
        return [
            ClaimTruthPair(
                claim=args.claim,
                truth=args.truth,
                pair_id="manual_001",
            )
        ]
    
    # Load from CSV
    all_pairs = load_claim_truth_pairs(args.csv)
    
    if not all_pairs:
        raise ValueError(f"No valid pairs found in {args.csv}")
    
    # Select subset if specified
    return select_pairs(all_pairs, indices=args.indices, count=args.count)


def run_debates(
    pairs: list[ClaimTruthPair],
    model: str,
    verbose: bool = True,
) -> list[DebateResult]:
    """Run debates on all pairs and return results."""
    engine = HackathonDebateEngine(model=model, verbose=verbose)
    results: list[DebateResult] = []
    
    for i, pair in enumerate(pairs, 1):
        if verbose:
            print(f"\n{'#' * 80}")
            print(f"# DEBATE {i} of {len(pairs)}")
            print(f"{'#' * 80}")
        
        result = engine.run(pair)
        results.append(result)
    
    return results


def print_summary(results: list[DebateResult]) -> None:
    """Print a summary of all debate results."""
    print("\n" + "=" * 60)
    print("SUMMARY OF ALL DEBATES")
    print("=" * 60)
    
    faithful_count = sum(1 for r in results if r.final_verdict.label == "Faithful")
    mutated_count = sum(1 for r in results if r.final_verdict.label == "Mutated")
    unclear_count = sum(1 for r in results if r.final_verdict.label == "Unclear")
    
    print(f"\nTotal debates: {len(results)}")
    print(f"  ✅ Faithful: {faithful_count}")
    print(f"  ❌ Mutated:  {mutated_count}")
    print(f"  ❓ Unclear:  {unclear_count}")
    
    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        verdict = result.final_verdict
        emoji = {"Faithful": "✅", "Mutated": "❌", "Unclear": "❓"}.get(verdict.label, "?")
        
        claim_preview = result.pair.claim[:60] + "..." if len(result.pair.claim) > 60 else result.pair.claim
        print(f"  {i}. {emoji} {verdict.label} ({verdict.confidence:.0%}) - {claim_preview}")
    
    print()


def main() -> None:
    """Main entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args()
    
    try:
        validate_args(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable must be set.", file=sys.stderr)
        sys.exit(1)
    
    # Get pairs to process
    try:
        pairs = get_pairs_to_process(args)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing {len(pairs)} claim/truth pair(s)...")
    
    # Determine model
    model = "gpt-4o" if args.premium else args.model
    
    # Run debates
    results = run_debates(pairs, model=model, verbose=not args.quiet)
    
    # Print summary
    if len(results) > 1:
        print_summary(results)
    
    # Save to file if requested
    if args.output:
        output_data = [asdict(r) for r in results]
        args.output.write_text(json.dumps(output_data, indent=2))
        print(f"Results saved to: {args.output}")


if __name__ == "__main__":
    main()
