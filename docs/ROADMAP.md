# Roadmap

## Milestone 1 — Single-claim “jury MVP”
Deliver:
- retrieval.mcp + sources.mcp + workspace.mcp (minimal tools)
- Agents: Manager, Claim, Planner, 2 Collectors, Critic, 3 Judges
- CLI: factcheck "claim"
- Strict JSON output + full tool-call logging

Exit criteria:
- No citations → cannot output Supported/Refuted
- Evidence comes only from allowlisted domains

## Milestone 2 — Multi-query + parallel collectors (your key requirement)
Deliver:
- Planner emits query bundles per claim atom
- Collectors run in parallel per source profile
- Deduping + evidence pack store
- Critic ranks evidence + flags conflicts + reports gaps

Exit criteria:
- Consistent multi-source coverage and conflict detection

## Milestone 3 — Multi-claim support + API
Deliver:
- Paragraph → atomic claims
- FastAPI endpoints:
  - POST /runs (start)
  - GET /runs/{id}/stream (SSE)
  - GET /runs/{id} (final report)

Exit criteria:
- Runs are reproducible and inspectable

## Milestone 4 — Frontend v1 (real UI)
Deliver:
- Next.js workspace UI:
  - streaming run console
  - claim cards + verdicts
  - evidence viewer (highlighted quotes)
  - judge votes panel
  - run history

Exit criteria:
- User can audit end-to-end path: claim → evidence → judges → final

## Milestone 5 — Governance + evals
Deliver:
- policy expansion tooling (manage allowlist tiers)
- regression eval harness + adversarial suite

Exit criteria:
- Changes to tools/policy are measured and don’t regress quality
