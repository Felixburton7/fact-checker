# checker_of_facts

Evidence‑bounded fact checking with an OpenAI Agents SDK jury. The CLI runs a multi‑agent pipeline that gathers evidence via MCP tools, consolidates it by domain, and produces a cited verdict.

## What this is

Use `checker_of_facts` when you want a **traceable** verdict that ties each conclusion back to evidence. The system:

- decomposes text into atomic claims
- searches and fetches evidence from the web
- summarizes evidence per domain
- issues a verdict with explicit citations

## How it works (pipeline)

1) **Manager** defines evidence policy (tier mix + citations required).
2) **Claim agent** splits the input into atomic claims.
3) **Retrieval planner** generates targeted search queries.
4) **Collectors** search, fetch, and extract quotes via MCP tools.
5) **Critic** ranks evidence by tier and quote quality.
6) **Judges** compare evidence summaries to the claim (negation‑aware).
7) **Aggregator** produces the final verdict with cited evidence ids.

Evidence is consolidated to **one multi‑sentence summary per domain** to keep sources diverse and reduce duplicates.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env
# edit .env with your keys

factcheck "The Moon is made of cheese."
```

## Configuration

Required:
- `OPENAI_API_KEY`

Recommended:
- `TAVILY_API_KEY`
- `BRAVE_API_KEY` (only used if Tavily fails or returns no results)

Optional:
- `OPENAI_MODEL` (default `gpt-4.1-mini`)
- `WORKSPACE_DIR` (default `.workspace`)
- `MCP_TRANSPORT` (default `stdio`)
- `MCP_RETRIEVAL_URL`, `MCP_SOURCES_URL`, `MCP_WORKSPACE_URL` (remote MCP servers; only used when transport is not `stdio`)

## Evidence tiers

- **A**: government/statistical/official bodies
- **B**: major reputable news and wire services
- **C**: reputable secondary sources
- **D**: low‑confidence or unknown sources

The system prefers A/B but can use C/D if that is all that is available. Confidence is adjusted accordingly.

## MCP tooling

The pipeline uses three MCP servers:

- **retrieval**: search, fetch, and quote extraction (Tavily + Brave fallback)
- **sources**: domain normalization, tiering, and allowlist checks
- **workspace**: evidence storage, cache, and run logs

By default these run in‑process via stdio. You can point to remote MCP servers by setting `MCP_TRANSPORT` and the MCP URL variables.

## Tests

```bash
.venv/bin/python -m pytest -q
```

For live web search tests:

```bash
TAVILY_API_KEY=... BRAVE_API_KEY=... .venv/bin/python -m pytest -q -s -m integration tests/test_retrieval_mcp.py
```

## Notes and limitations

- “Current” claims depend on the evidence retrieval date; stale evidence lowers confidence.
- Evidence is summarized and not the full page text.
- Verdicts are evidence‑first; no uncited facts are allowed.
