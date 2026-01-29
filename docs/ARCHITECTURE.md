# Architecture

## Components
1) Backend (Python)
- Agents SDK agents
- MCP client registry (connects to mcp servers)
- Orchestrator (manager flow)
- FastAPI API + SSE event stream
- Storage: local sqlite/postgres later (runs, evidence packs, outputs)

2) MCP Servers
- retrieval.mcp: search/fetch/extract/quote
- sources.mcp: allowlist + tiers + policy checks
- workspace.mcp: cache, run logs, evidence pack store/load

3) Frontend (Next.js)
- Run workspace (streaming)
- Claim list + verdict chips
- Evidence panel (quotes, metadata, open source)
- Jury panel (each judge vote + rationale)
- History (past runs)

## Strict boundary
Agents can only call MCP tools for external data.
Backend can call DB and internal services, but agents see them only through MCP abstractions.

## Streaming model
Backend emits SSE events:
- run_started
- claim_decomposed
- retrieval_planned
- evidence_collected
- evidence_scored
- judge_voted
- verdict_aggregated
- run_completed
- error
