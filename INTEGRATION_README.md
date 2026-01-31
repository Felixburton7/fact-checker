# FactTrace Integration Guide

This document explains how to run the integrated FactTrace system with the frontend (Truth Jury) and backend (Checker of Claims).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (React)                          │
│                   truth-jury-main                               │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Index Page  │───▶│ LiveDebate   │───▶│   VerdictCard    │  │
│  │  (Select     │    │    Page      │    │   (Final         │  │
│  │   Claims)    │    │  (Streaming) │    │    Result)       │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│                              │                                  │
│                              │ HTTP/SSE                         │
│                              ▼                                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ Server-Sent Events
                               │ (Real-time streaming)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND (Python)                          │
│                   checker-of-claims                             │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   FastAPI    │───▶│   Debate     │───▶│   OpenAI Agents  │  │
│  │     API      │    │   Engine     │    │   (Jury + Judge) │  │
│  │  /api.py     │    │              │    │                  │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start the Backend API

```bash
# Navigate to the backend directory
cd checker-of-claims

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Set your OpenAI API key
export OPENAI_API_KEY="your-key-here"
# Or create a .env file with: OPENAI_API_KEY=your-key-here

# Start the API server
python -m checker_of_facts.api
# Or use: api  (if installed as a script)
```

The API will be available at `http://localhost:8000`

### 2. Start the Frontend

```bash
# Navigate to the frontend directory
cd truth-jury-main

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Endpoints

### `POST /debate/stream`
Stream a debate in real-time via Server-Sent Events.

**Request:**
```json
{
  "claim": "The external claim to fact-check",
  "truth": "The internal fact (ground truth)",
  "model": "gpt-4o-mini"  // optional, defaults to gpt-4o-mini
}
```

**Response:** Server-Sent Events stream with debate events.

### `POST /debate/sync`
Run a complete debate and return the full result (blocking).

### `GET /personas`
Get the list of available jury personas.

### `GET /health`
Health check endpoint.

## Frontend Routes

| Route | Description |
|-------|-------------|
| `/` | Home page - Browse and select claims |
| `/debate/:id` | Live debate page using backend API |
| `/demo/:id` | Demo/offline mode with pre-scripted debates |

## Environment Variables

### Backend
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `PORT`: Server port (default: 8000)

### Frontend
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

## Model Options

When starting a debate, you can specify the model:

- `gpt-4o-mini` (default) - Fast and cost-effective
- `gpt-4o` - Higher quality, more expensive
- `gpt-4.1-mini` - Alternative mini model
- `gpt-4.1` - Alternative premium model

## Features

### Real-time Streaming
The debate unfolds in real-time via Server-Sent Events. Each juror speaks one at a time, with typing indicators showing who's currently deliberating.

### Multi-Agent Jury System
Five distinct AI personas debate each claim:
- **The Skeptic** - Deeply critical, challenges everything
- **The Academic** - Research-focused, demands evidence  
- **The Journalist** - Source-focused, detects spin
- **The Pragmatist** - Practical implications focus
- **The Ethicist** - Moral and intent analysis

### Two-Round Debate Structure
1. **Introduction** - Moderator frames the discussion
2. **Round 1** - Each juror shares initial analysis
3. **Moderator Summary** - Key points and direction for Round 2
4. **Round 2** - Jurors refine positions based on discussion
5. **Final Verdict** - Judge delivers the final decision

### Verdict Types
- **Faithful** ✅ - Claim accurately represents the fact
- **Mutated** ❌ - Claim distorts or misrepresents the fact
- **Ambiguous** ❓ - Insufficient evidence to determine

## Development

### Backend Development
```bash
cd checker-of-claims
pip install -e ".[dev]"  # Install dev dependencies
ruff check .              # Lint
ruff format .            # Format
pytest                   # Test
```

### Frontend Development
```bash
cd truth-jury-main
npm run dev      # Development server
npm run build    # Production build
npm run test     # Run tests
npm run lint     # Lint code
```

## Troubleshooting

### "API Offline" in Frontend
- Ensure the backend is running (`python -m checker_of_facts.api`)
- Check that CORS is properly configured
- Verify the API URL matches (default: localhost:8000)

### OpenAI API Errors
- Verify your API key is set correctly
- Check your OpenAI account has available credits
- Try a different model (e.g., `gpt-4o-mini`)

### Slow Debates
- The debate involves multiple AI calls, which can take 30-60 seconds total
- Use `gpt-4o-mini` for faster responses
- Consider the `/demo/:id` route for pre-recorded debates

## License

MIT License - Built for the FactTrace Hackathon @ University of Cambridge
