# Factcheck Agent — Project Plan

## Goal
Given a user claim (or paragraph), return a fact-check report with:
- Verdict: Supported / Refuted / NotEnoughEvidence / Mixed
- Confidence (0–1) calibrated by evidence quality + judge agreement
- Evidence: quoted snippets + URLs + retrieval timestamps + source tier
- Short structured rationale and a minority report if judges disagree
- Strict rule: **No citation → no factual assertion**

## Non-negotiables
- Agents may not browse directly. All external access is via **MCP tools**.
- Evidence must come from allowlisted trusted domains (Tier A/B/C).
- Every verdict must cite EvidenceItem IDs. No fabricated citations.

## Primary stack
Backend:
- Python 3.11
- OpenAI Agents SDK (agents, handoffs, tracing)
- MCP servers (retrieval, policy, workspace)
- FastAPI + SSE (stream run events to UI)
- Pydantic v2 (strict schemas)
- httpx + trafilatura (fetch + clean extraction)
- pytest + ruff + mypy (quality gates)

Frontend:
- Next.js + React
- Tailwind + shadcn/ui
- Evidence viewer with quote highlighting and source metadata
- Streaming run UI (SSE)

Optional:
- LangGraph for deterministic “state machine” orchestration around Agents SDK calls (not required).

## Agent lineup (manager + experts)
Manager Agent (Orchestrator)
- Controls flow, budgets, aggregation, and schema validation
- Tools: workspace/cache/log/schema; **no web tools**

Claim Agent (Decomposer)
- Splits input into atomic claims + claim type (numeric/date/event/science/etc.)

Retrieval Planner Agent
- Produces multiple query variants per atomic claim
- Produces a required source mix (e.g., Tier A + Tier B)

Evidence Collector Agents (parallel, specialized)
- News Collector (Tier B)
- Gov/Stats Collector (Tier A)
- Scholarly/Registry Collector (Tier A-ish)
- Reference Collector (Tier C)
(Each collector has its own MCP tool profile / source filter)

Critic Agent (Scorer)
- Scores evidence items and sources:
  - tier, relevance, recency, directness, extract quality, conflict detection
- Outputs ranked evidence set + coverage gaps + flags

Judge Agents (multi-judge jury)
- Strict Judge (high bar, prefers Tier A)
- Pragmatic Judge (accepts strong Tier B if Tier A unavailable)
- Skeptical Judge (ambiguity/timeframe/definition hawk)
Optional: Quant Judge / Causality Judge

Aggregator (Manager step)
- Computes final verdict using judge votes + weighted evidence quality
- Produces minority report if disagreement exists

## Orchestration flow (per atomic claim)
1) Decompose → atomic claims
2) Retrieval plan → query bundles + source requirements
3) Parallel collection → evidence packs
4) Critic scoring → ranked evidence + conflicts + gaps
5) Jury judging → multiple verdicts + rationales
6) Aggregate → final verdict + confidence + minority report
7) Emit strict JSON matching SCHEMAS.md

## Deliverables
- CLI: `factcheck "claim"`
- API: start run + stream events + fetch final report
- UI: run workspace + claim cards + evidence panel + jury panel + history
