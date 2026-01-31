# Roadmap

## Milestone 1 — Single-claim “jury MVP”
Deliver:
- Internal-knowledge-only agents (no MCP tools)
- Agents: Claim + Moderator + 5 Jurors
- CLI: factcheck "claim"
- Debate transcript + moderator verdict output

Exit criteria:
- Verdicts are produced without external data

## Milestone 2 — Multi-query + parallel collectors (your key requirement)
Deliver:
- (Removed; no evidence collection in current scope)

Exit criteria:
- N/A

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
  - claim viewer (judge rationales)
  - judge votes panel
  - run history

Exit criteria:
- User can audit end-to-end path: claim → judges → final

## Milestone 5 — Governance + evals
Deliver:
- policy expansion tooling (manage allowlist tiers)
- regression eval harness + adversarial suite

Exit criteria:
- Changes to tools/policy are measured and don’t regress quality
