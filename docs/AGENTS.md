# AGENTS.md

## Read first
- docs/PROJECT_PLAN.md
- docs/ARCHITECTURE.md
- docs/TRUST_POLICY.md
- docs/SCHEMAS.md
- docs/ROADMAP.md
- PLANS.md

## Project rules
- No external data access or web retrieval.
- Moderator and jurors rely on internal model knowledge.
- Debate is turn-based and deterministic.

## Juror personas and order
Fixed turn order (deterministic):
1) **Juror A — Analyst**: careful, analytical, defines terms and assumptions.
2) **Juror B — Skeptic**: challenges weak claims, flags ambiguity and edge cases.
3) **Juror C — Pragmatist**: focuses on practical interpretation and likely intent.
4) **Juror D — Historian**: adds context from historical knowledge and precedent.
5) **Juror E — Contrarian**: stress-tests the majority view and proposes alternatives.

Each juror must consider prior turns before speaking while keeping their persona.

## Commands
Backend:
- Install: `uv sync`
- Lint: `uv run ruff check .`
- Typecheck: `uv run mypy .`
- Test: `uv run pytest -q`

Frontend:
- Install: `pnpm i`
- Dev: `pnpm dev`

## Working style
- Keep each PR focused on a single milestone deliverable.
- Add tests for tool policy enforcement and schema validity.
