# Factcheck Agent — Project Plan

## Goal
Given a user claim (or paragraph), return a fact-check report with:
- Debate transcript (5 juror turns)
- Verdict: Supported / Refuted / NotEnoughEvidence / Mixed
- Confidence (0–1) calibrated by juror agreement
- Moderator rationale and minority notes if relevant

## Non-negotiables
- Agents may not browse directly. No external access is permitted.
- Verdicts are based on internal model knowledge.
- Debate order is deterministic and fixed.

## Primary stack
Backend:
- Python 3.11
- OpenAI Agents SDK (agents, handoffs, tracing)
- FastAPI + SSE (stream run events to UI)
- Pydantic v2 (strict schemas)
- pytest + ruff + mypy (quality gates)

Frontend:
- Next.js + React
- Tailwind + shadcn/ui
- Streaming run UI (SSE)

Optional:
- LangGraph for deterministic “state machine” orchestration around Agents SDK calls (not required).

## Agent lineup (moderator + jurors)
Moderator Agent (Orchestrator)
- Controls flow, runs the debate, and issues final verdict

Claim Agent (Decomposer)
- Splits input into atomic claims + claim type (numeric/date/event/science/etc.)

Juror Agents (5 total)
- Each juror has a distinct personality and reasoning style.
- Each juror must consider prior juror turns before responding.

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
2) Debate → fixed 5 juror turns (deterministic order)
3) Moderator verdict → final verdict + confidence + rationale
4) Emit strict JSON matching SCHEMAS.md

## Deliverables
- CLI: `factcheck "claim"`
- API: start run + stream events + fetch final report
- UI: run workspace + claim cards + debate panel + moderator verdict + history
