#!/bin/bash
# Quick script to run the hackathon debate system
# Usage: ./run_hackathon.sh [options]

set -e

# Change to the checker-of-claims directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update package
pip install -e . -q

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set. Create a .env file or export the variable."
    exit 1
fi

# Run the hackathon CLI
python -m checker_of_facts.hackathon_cli "$@"
