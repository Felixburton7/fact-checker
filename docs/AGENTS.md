# AGENTS.md

## Read first
- docs/PROJECT_PLAN.md
- docs/ARCHITECTURE.md
- docs/TRUST_POLICY.md
- docs/SCHEMAS.md
- docs/ROADMAP.md
- PLANS.md

## Project rules
- External data ONLY through MCP tools.
- Enforce allowlist + tiering via sources.mcp.
- Strict citations: no evidence ID, no assertion.

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
