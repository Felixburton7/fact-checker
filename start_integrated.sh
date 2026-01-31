#!/bin/bash

# FactTrace Integration Startup Script
# This script starts both the backend API and frontend development servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              FactTrace Integration Startup                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR"
FACTRACE_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$FACTRACE_DIR/truth-jury-frontend"

# Check if frontend directory exists (try alternate locations)
if [ ! -d "$FRONTEND_DIR" ]; then
    FRONTEND_DIR="$HOME/Downloads/truth-jury-main"
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Error: Frontend directory not found!${NC}"
    echo "Expected at: $FACTRACE_DIR/truth-jury-frontend"
    echo "Or at: $HOME/Downloads/truth-jury-main"
    exit 1
fi

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    if [ -f "$BACKEND_DIR/.env" ]; then
        source "$BACKEND_DIR/.env"
    fi
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${YELLOW}Warning: OPENAI_API_KEY not set!${NC}"
        echo "Set it with: export OPENAI_API_KEY='your-key-here'"
        echo "Or create a .env file in $BACKEND_DIR"
        echo ""
    fi
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo -e "${GREEN}Starting Backend API...${NC}"
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment and install dependencies
source .venv/bin/activate
pip install -e . --quiet

# Start the API server in the background
echo -e "${GREEN}Starting API server on http://localhost:8000${NC}"
python -m checker_of_facts.api &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 2

# Start Frontend
echo ""
echo -e "${GREEN}Starting Frontend...${NC}"
cd "$FRONTEND_DIR"

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
fi

# Start the frontend development server
echo -e "${GREEN}Starting frontend on http://localhost:5173${NC}"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Services are running!${NC}"
echo ""
echo -e "  ${BLUE}Backend API:${NC}  http://localhost:8000"
echo -e "  ${BLUE}Frontend:${NC}     http://localhost:5173"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
