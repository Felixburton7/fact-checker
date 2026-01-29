# Trust Policy (Bounded Evidence)

## Tiers
Tier A (authoritative / primary)
- Government/statistical agencies, regulators, courts
- Academic registries/metadata (Crossref/OpenAlex), PubMed
- Company primary documents (SEC filings, investor reports)

Tier B (high-quality news / institutions)
- Reuters, AP, BBC, FT, Economist, etc.
- Major newspapers with established editorial standards (treated as secondary)

Tier C (reference)
- Britannica, Wikipedia (supporting context, not sole authority for contentious claims)

## Rules
- Retrieval tools must enforce allowlisted domains and attach tier metadata.
- Prefer ≥2 independent sources; prefer including Tier A when feasible.
- If evidence conflicts, judges must surface the conflict and reduce confidence.
- No “common knowledge” exceptions. If it matters, cite it.

## Implementation
- `sources.mcp` owns:
  - allowlist/denylist
  - domain→tier mapping
  - per-claim-type requirements (e.g., medical claims require Tier A)
- `retrieval.mcp` must refuse to fetch non-allowed domains.
