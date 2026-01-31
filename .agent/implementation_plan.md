# Implementation Plan: Multi-Agent Jury Debate System

## Overview

This document describes the implementation of a multi-agent jury debate system for the Cambridge DIS Hackathon. The system evaluates whether external claims are faithful representations of internal facts.

## Task Requirements (From User Prompt)

| Requirement | Implementation |
|-------------|----------------|
| Multi-agent debate with Jurors | ✅ 5 distinct juror personas |
| Each Juror has different personality | ✅ Skeptic, Pedant, Pragmatist, Devil's Advocate, Context Expert |
| Random talking order | ✅ Shuffled order per round |
| Each Juror gets 2 turns | ✅ 2 rounds of debate |
| Consider prior conversation | ✅ Prior turns included in agent input |
| Moderator summarizes after Round 1 | ✅ ModeratorSummary between rounds |
| Moderator sets tone for next iteration | ✅ Guidance included in Round 2 context |
| Final verdict by Moderator | ✅ ModeratorFinalVerdict at end |
| Print output as agents speak | ✅ Real-time colored terminal output |

## Files Created

### Core Implementation

1. **`hackathon_models.py`** - Data models
   - `ClaimTruthPair`: Input pair structure
   - `JurorPersona`: Juror personality definition
   - `DebateTurn`: Single juror argument
   - `DebateRound`: Collection of turns in a round
   - `ModeratorSummary`: Mid-debate summary
   - `ModeratorFinalVerdict`: Final verdict with reasoning
   - `DebateResult`: Complete debate output

2. **`hackathon_agents.py`** - Agent definitions
   - `build_juror_agent()`: Creates personality-driven juror agents
   - `build_moderator_summary_agent()`: Mid-debate summarizer
   - `build_moderator_verdict_agent()`: Final verdict agent
   - `build_hackathon_registry()`: Builds complete agent registry

3. **`hackathon_engine.py`** - Debate orchestration
   - `HackathonDebateEngine.run()`: Main entry point
   - Implements random juror ordering
   - Handles 2 rounds with moderator intervention
   - Real-time colored output printing

4. **`hackathon_cli.py`** - Command-line interface
   - Supports manual claim/truth input
   - Supports CSV file input
   - Model selection (cheap vs premium)
   - Output saving

5. **`data_loader.py`** - CSV data loading
   - Parses Polaris.csv format
   - Subset selection by count or indices

### Support Files

- **`HACKATHON_README.md`** - Usage documentation
- **`run_hackathon.sh`** - Quick start script
- Updated **`pyproject.toml`** with `hackathon` entry point

## Juror Personas

| ID | Name | Description |
|----|------|-------------|
| `skeptic` | The Skeptic | Deeply critical, looks for logical fallacies and misrepresentations |
| `pedant` | The Pedantic Fact-Checker | Obsessed with precision, focuses on exact numbers and dates |
| `pragmatist` | The Common Sense Judge | Considers practical meaning and average reader interpretation |
| `devil_advocate` | The Devil's Advocate | Takes opposing view to stress-test consensus |
| `context_expert` | The Context Expert | Identifies missing context and implications |

## Debate Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     DEBATE SESSION                           │
├─────────────────────────────────────────────────────────────┤
│ 1. Display claim/truth pair                                  │
├─────────────────────────────────────────────────────────────┤
│ 2. ROUND 1                                                   │
│    ├─ Randomly order 5 jurors                                │
│    ├─ Each juror speaks (considers prior turns)              │
│    └─ Print each turn in real-time                           │
├─────────────────────────────────────────────────────────────┤
│ 3. MODERATOR SUMMARY                                         │
│    ├─ Summarize key points                                   │
│    ├─ Identify agreements/disagreements                      │
│    └─ Provide guidance for Round 2                           │
├─────────────────────────────────────────────────────────────┤
│ 4. ROUND 2                                                   │
│    ├─ New random order for jurors                            │
│    ├─ Each juror speaks (considers ALL prior + summary)      │
│    └─ Print each turn in real-time                           │
├─────────────────────────────────────────────────────────────┤
│ 5. FINAL VERDICT                                             │
│    ├─ Label: Faithful / Mutated / Unclear                    │
│    ├─ Confidence score                                       │
│    ├─ Key arguments for each side                            │
│    └─ Detailed reasoning                                     │
└─────────────────────────────────────────────────────────────┘
```

## Usage Examples

```bash
# Test with one pair from CSV
python -m checker_of_facts.hackathon_cli \
    --csv ../cambridge-dis-hackathon/Polaris.csv \
    --count 1

# Process 5 pairs (recommended for hackathon)
python -m checker_of_facts.hackathon_cli \
    --csv ../cambridge-dis-hackathon/Polaris.csv \
    --count 5

# Use premium model for demo
python -m checker_of_facts.hackathon_cli \
    --csv ../cambridge-dis-hackathon/Polaris.csv \
    --count 5 \
    --premium

# Save results for later
python -m checker_of_facts.hackathon_cli \
    --csv ../cambridge-dis-hackathon/Polaris.csv \
    --count 5 \
    --output results.json
```

## Model Costs (Approximate)

| Model | Speed | Cost | When to Use |
|-------|-------|------|-------------|
| `gpt-4.1-mini` | Fast | ~$0.01/debate | Development, testing |
| `gpt-4o` | Medium | ~$0.10/debate | Demo, presentation |

With 5 jurors × 2 rounds + 2 moderator calls = 12 API calls per debate.
For 5 debates: ~60 API calls total.

## Judging Criteria Alignment

| Criterion | How the System Addresses It |
|-----------|----------------------------|
| **Agent Design (30%)** | 5 distinct personas with meaningful roles; jurors actually debate and reference each other |
| **Reasoning & Explanation (30%)** | Detailed rationale bullets, arguments for/against, confidence levels |
| **Data Understanding (20%)** | CLI supports selecting specific interesting pairs via `--indices` |
| **Demo Clarity (20%)** | Real-time colored output shows debate progression clearly |
