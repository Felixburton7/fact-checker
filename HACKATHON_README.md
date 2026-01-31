# Cambridge DIS Hackathon: Multi-Agent Jury Debate System

## Overview

This extension to `checker_of_facts` implements a **multi-agent jury debate system** for the Cambridge DIS Hackathon. The system evaluates whether an **external claim** (e.g., a tweet or headline) is a **faithful representation** of an **internal fact** (ground truth) or whether it's been **mutated** (distorted, exaggerated, or missing context).

## Key Features

### 🎭 Distinct Juror Personas
Five jurors with unique personalities debate each claim:

| Juror | Persona | Role |
|-------|---------|------|
| **The Skeptic** | Deeply critical | Challenges everything, looks for fallacies |
| **The Pedantic Fact-Checker** | Precision-obsessed | Focuses on exact numbers, dates, wording |
| **The Common Sense Judge** | Pragmatist | Considers average reader interpretation |
| **The Devil's Advocate** | Contrarian | Stress-tests consensus, argues opposite view |
| **The Context Expert** | Big-picture thinker | Identifies missing context and implications |

### 🔄 Two-Round Debate Structure
1. **Round 1**: Each juror speaks once (random order)
2. **Moderator Summary**: Summarizes points, identifies agreements/disagreements, sets tone for Round 2
3. **Round 2**: Each juror speaks again (new random order), considering all prior arguments
4. **Final Verdict**: Moderator delivers conclusion with reasoning

### 📋 Output
- Real-time colored terminal output as each juror speaks
- Final verdict: **Faithful**, **Mutated**, or **Unclear**
- Confidence level and detailed reasoning
- Summary of arguments for both sides

## Quick Start

```bash
# 1. Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -e .

# 2. Set your API key
export OPENAI_API_KEY="your-key-here"
# Or create a .env file with: OPENAI_API_KEY=your-key-here

# 3. Run a single debate
python -m checker_of_facts.hackathon_cli \
    --claim "Germany had less than 13,200 cases..." \
    --truth "As of 19 March 2020, Germany has reported 13,083 cases..."

# 4. Run on CSV data (recommended: 5 pairs)
python -m checker_of_facts.hackathon_cli \
    --csv ../cambridge-dis-hackathon/Polaris.csv \
    --count 5

# 5. For demo day, use premium model
python -m checker_of_facts.hackathon_cli \
    --csv ../cambridge-dis-hackathon/Polaris.csv \
    --count 5 \
    --premium
```

## CLI Options

```
Input Options:
  --claim TEXT         External claim text
  --truth TEXT         Internal fact / ground truth  
  --csv PATH           Path to CSV file with claim/truth pairs
  --count N            Number of pairs to process from CSV
  --indices 1 3 5      Specific pair indices (1-indexed)

Model Options:
  --model MODEL        OpenAI model (default: gpt-4.1-mini)
  --premium            Use gpt-4o for demo

Output Options:
  --quiet              Only show final JSON
  --output PATH        Save results to JSON file
```

## Example Output

```
════════════════════════════════════════════════════════════
                    JURY DEBATE SESSION
════════════════════════════════════════════════════════════

📋 INTERNAL FACT (Ground Truth):
   As of 19 March 2020, Germany has reported 13,083 cases and 31 deaths...

🔍 EXTERNAL CLAIM (Under Review):
   German had less than 13,200 coronavirus cases with less than 32 deaths...

════════════════════════════════════════════════════════════
                         ROUND 1
════════════════════════════════════════════════════════════
Speaking order: pragmatist, skeptic, context_expert, devil_advocate, pedant

🎭 The Common Sense Judge (pragmatist)
   Round 1, Turn 1
   The claim captures the essence of the ground truth...

🎭 The Skeptic (skeptic)
   Round 1, Turn 2
   I must challenge the use of "less than" as a framing device...

[... more juror turns ...]

────────────────────────────────────────────────────────────
⚖️  MODERATOR SUMMARY (After Round 1)
────────────────────────────────────────────────────────────

Summary: The jurors are divided on whether the numeric framing...

════════════════════════════════════════════════════════════
                         ROUND 2
════════════════════════════════════════════════════════════

[... jurors reconsider and refine their arguments ...]

════════════════════════════════════════════════════════════
⚖️  FINAL VERDICT
════════════════════════════════════════════════════════════

✅ VERDICT: Faithful
   Confidence: 75%

Summary: While there are minor framing differences, the claim...
```

## Architecture

```
checker_of_facts/
├── hackathon_models.py    # Data models for debate system
├── hackathon_agents.py    # Agent definitions with personas
├── hackathon_engine.py    # Debate orchestration engine
├── hackathon_cli.py       # Command-line interface
└── data_loader.py         # CSV data loading utilities
```

## Tips for the Hackathon

1. **Choose interesting pairs**: Pick cases with ambiguity that will spark debate
2. **Use cheap model for testing**: `gpt-4.1-mini` costs ~10x less than `gpt-4o`
3. **Switch to premium for demo**: Use `--premium` flag for final presentation
4. **Save results**: Use `--output results.json` to preserve debate transcripts
