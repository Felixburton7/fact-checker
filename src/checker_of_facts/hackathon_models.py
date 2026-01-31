"""
Models for the Cambridge DIS Hackathon multi-agent jury debate system.

Key differences from base models:
- Supports multiple debate rounds (iterations)
- Includes moderator mid-debate summary
- Tracks juror order per round (randomized)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

VerdictLabel = Literal["Faithful", "Mutated", "Unclear"]


@dataclass(frozen=True)
class ClaimTruthPair:
    """A pair of external claim and internal fact (ground truth)."""
    claim: str  # External claim (e.g., tweet, headline)
    truth: str  # Internal fact (source truth)
    pair_id: str = ""


@dataclass(frozen=True)
class JurorPersona:
    """Definition of a juror's personality and debate style."""
    id: str
    name: str
    persona: str
    description: str


@dataclass(frozen=True)
class DebateTurn:
    """A single turn in the debate by a juror."""
    juror_id: str
    juror_name: str
    persona: str
    round_number: int  # 1 or 2
    turn_index: int  # Position within the round
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class ModeratorSummary:
    """Moderator's mid-debate summary after round 1."""
    summary: str
    key_points: list[str]
    areas_of_agreement: list[str]
    areas_of_disagreement: list[str]
    guidance_for_next_round: str


@dataclass(frozen=True)
class ModeratorFinalVerdict:
    """Moderator's final verdict after all debate rounds."""
    label: VerdictLabel
    confidence: float
    summary: str
    rationale_bullets: list[str]
    key_arguments_for_faithful: list[str]
    key_arguments_for_mutated: list[str]
    final_reasoning: str


@dataclass(frozen=True)
class DebateRound:
    """A single round of debate with all juror turns."""
    round_number: int
    juror_order: list[str]  # Order of juror IDs for this round
    turns: list[DebateTurn]


@dataclass(frozen=True)
class DebateResult:
    """Complete result of a multi-round jury debate."""
    pair: ClaimTruthPair
    rounds: list[DebateRound]
    moderator_summary: ModeratorSummary | None  # After round 1
    final_verdict: ModeratorFinalVerdict
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Default juror personas for the hackathon
DEFAULT_JUROR_PERSONAS: list[JurorPersona] = [
    JurorPersona(
        id="skeptic",
        name="The Skeptic",
        persona="skeptic",
        description=(
            "You are deeply critical and question everything. You look for logical fallacies, "
            "missing context, and potential misrepresentations. You are not easily convinced and "
            "will challenge claims that seem too good to be true or lack proper evidence."
        ),
    ),
    JurorPersona(
        id="pedant",
        name="The Pedantic Fact-Checker",
        persona="pedant",
        description=(
            "You are obsessed with precision and accuracy. You focus on exact numbers, dates, "
            "and specific wording. Even small differences in figures or phrasing matter to you. "
            "You believe that 'technically correct' matters and will call out any numeric or "
            "temporal discrepancies."
        ),
    ),
    JurorPersona(
        id="pragmatist",
        name="The Common Sense Judge",
        persona="pragmatist",
        description=(
            "You focus on the practical meaning and likely interpretation by an average reader. "
            "You care about whether the overall message is preserved, not just technical accuracy. "
            "You consider what the original source intended to convey and whether the claim "
            "captures that essence."
        ),
    ),
    JurorPersona(
        id="devil_advocate",
        name="The Devil's Advocate",
        persona="devil_advocate",
        description=(
            "You deliberately take the opposing view to stress-test the consensus. "
            "If others are leaning toward 'Faithful', you argue for 'Mutated' and vice versa. "
            "You believe that truth emerges through rigorous debate and challenge."
        ),
    ),
    JurorPersona(
        id="context_expert",
        name="The Context Expert",
        persona="context_expert",
        description=(
            "You specialize in understanding broader context and implications. You consider "
            "what information might be missing, what assumptions are being made, and how "
            "the claim might be interpreted differently by different audiences. You look "
            "for subtle shifts in meaning that come from omitting context."
        ),
    ),
]
