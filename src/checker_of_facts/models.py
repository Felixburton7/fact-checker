from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

ClaimType = Literal["numeric", "date", "event", "scientific", "other"]
VerdictLabel = Literal["Supported", "Refuted", "NotEnoughEvidence", "Mixed"]
SourceTier = Literal["A", "B", "C", "D"]
SourceProfile = Literal["gov_stats", "news", "reference", "scholarly"]


@dataclass(frozen=True)
class ClaimInput:
    text: str
    locale: str | None = None
    user_context: dict[str, Any] | None = None


@dataclass(frozen=True)
class ClaimAtom:
    id: str
    text: str
    type: ClaimType
    entities: list[str] = field(default_factory=list)
    timeframe: str | None = None
    numeric_values: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class ClaimBundle:
    raw_text: str
    claims: list[ClaimAtom]


@dataclass(frozen=True)
class RetrievalQueryBundle:
    claim_id: str
    exact_phrase: str
    entity_predicate: str
    timeframe_query: str | None
    debunk_query: str | None
    source_mix_requirement: str


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    url: str
    domain: str
    quote: str
    tier: SourceTier
    title: str | None
    published_at: str | None
    retrieved_at: str
    context: str | None
    hash: str
    source_profile: SourceProfile


@dataclass(frozen=True)
class EvidencePack:
    claim_atom_id: str
    collector_name: str
    items: list[EvidenceItem]
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CriticResult:
    claim_id: str
    ranked_items: list[EvidenceItem]
    flags: list[str]
    coverage_gaps: list[str]


@dataclass(frozen=True)
class JudgeVerdict:
    claim_id: str
    judge_id: str
    label: VerdictLabel
    confidence: float
    rationale_bullets: list[str]
    cited_evidence_ids: list[str]
    missing_evidence: list[str]


@dataclass(frozen=True)
class FinalVerdict:
    label: VerdictLabel
    confidence: float
    consensus_rationale: list[str]
    cited_evidence_ids: list[str]
    disagreements: list[str] | None = None
    minority_report: str | None = None


@dataclass(frozen=True)
class ClaimResult:
    claim: ClaimAtom
    debate: list["JurorTurn"]
    moderator_verdict: "ModeratorVerdict"
    final_verdict: FinalVerdict


@dataclass(frozen=True)
class FactCheckReport:
    run_id: str
    input: ClaimInput
    claims: list[ClaimResult]
    overall_summary: str | None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class ManagerDirective:
    source_mix_requirement: str
    require_citations: bool
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class JurorTurn:
    juror_id: str
    persona: str
    turn_index: int
    content: str
    reactions: list["JurorReaction"] = field(default_factory=list)


@dataclass(frozen=True)
class ModeratorVerdict:
    label: VerdictLabel
    confidence: float
    rationale_bullets: list[str]
    minority_report: str | None = None


@dataclass(frozen=True)
class JurorReaction:
    target_juror_id: str
    target_turn_index: int
    reaction: Literal["like", "dislike"]
