# Architecture

## Components
1) Backend (Python)
- Agents SDK agents
- Orchestrator (claim → juror debate → moderator verdict)
- FastAPI API + SSE event stream
- Storage: local sqlite/postgres later (runs, outputs)

2) Frontend (Next.js)
- Run workspace (streaming)
- Claim list + verdict chips
- Debate panel (juror turns + moderator verdict)
- History (past runs)

## Strict boundary
Agents do not call external tools; all judgments are internal.

## Streaming model
Backend emits SSE events:
- run_started
- claim_decomposed
- debate_turn
- moderator_verdict
- run_completed
- error
