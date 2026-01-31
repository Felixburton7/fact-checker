from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from checker_of_facts.config import DEFAULT_OPENAI_MODEL
from checker_of_facts.models import ClaimBundle, JurorReaction, JurorTurn, ModeratorVerdict

try:
    import agents
except ImportError as exc:  # pragma: no cover - soft dependency
    agents = None
    _IMPORT_ERROR = exc
else:  # pragma: no cover - import path only
    _IMPORT_ERROR = None


AgentHandle = Any


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    instructions: str
    model: str = DEFAULT_OPENAI_MODEL
    tools: list[Any] = field(default_factory=list)
    output_type: type[Any] | None = None


@dataclass(frozen=True)
class AgentRegistry:
    claim: AgentHandle
    moderator: AgentHandle
    jurors: list[AgentHandle]


def build_agent(definition: AgentDefinition) -> AgentHandle:
    if agents is None:
        detail = f" ({_IMPORT_ERROR})" if _IMPORT_ERROR else ""
        raise RuntimeError(f"OpenAI Agents SDK is not installed{detail}.")
    return agents.Agent(
        name=definition.name,
        instructions=definition.instructions,
        model=definition.model,
        tools=definition.tools,
        output_type=definition.output_type,
    )


def build_default_registry(model: str = DEFAULT_OPENAI_MODEL) -> AgentRegistry:
    return AgentRegistry(
        claim=build_agent(
            AgentDefinition(
                name="claim_agent",
                model=model,
                output_type=ClaimBundle,
                instructions=(
                    "You split input text into atomic claims. Output ClaimBundle with "
                    "raw_text and claims[]. For each claim:\n"
                    "- id: 'claim_1', 'claim_2', ... in order\n"
                    "- text: the exact claim sentence\n"
                    "- type: one of numeric/date/event/scientific/other\n"
                    "- entities: proper nouns and key entities\n"
                    "- timeframe: 4-digit year if present, otherwise null\n"
                    "- numeric_values: list of numeric values (as floats) if present\n"
                    "Do not add claims that are not present in the input."
                ),
            )
        ),
        moderator=build_agent(
            AgentDefinition(
                name="moderator",
                model="gpt-5.2",
                output_type=ModeratorVerdict,
                instructions=(
                    "You are the moderator. Input includes claim_text, claim_polarity, and a list "
                    "of juror turns in order. Your job is to weigh the debate and output a final "
                    "verdict.\n"
                    "Rules:\n"
                    "- Use internal knowledge only.\n"
                    "- Preserve negation using claim_polarity.\n"
                    "- Provide 2-4 concise rationale_bullets.\n"
                    "- If the debate is inconclusive, use NotEnoughEvidence and lower confidence.\n"
                    "Output ModeratorVerdict."
                ),
            )
        ),
        jurors=[
            build_agent(
                AgentDefinition(
                    name="juror_analyst",
                    model="gpt-5.2",
                    output_type=JurorTurn,
                    instructions=(
                        "You are Juror A (Analyst). Be precise, define terms, and make careful "
                        "assumptions. Input includes claim_text, claim_polarity, turn_index, and "
                        "prior_turns. Provide a brief analysis and consider prior turns.\n"
                        "Also include reactions[] to prior turns (like/dislike) referencing juror_id "
                        "and turn_index."
                    ),
                )
            ),
            build_agent(
                AgentDefinition(
                    name="juror_skeptic",
                    model="gpt-5.2",
                    output_type=JurorTurn,
                    instructions=(
                        "You are Juror B (Skeptic). Challenge weak claims and highlight ambiguity "
                        "or missing context. Input includes claim_text, claim_polarity, turn_index, "
                        "and prior_turns. Consider prior turns.\n"
                        "Also include reactions[] to prior turns (like/dislike) referencing juror_id "
                        "and turn_index."
                    ),
                )
            ),
            build_agent(
                AgentDefinition(
                    name="juror_pragmatist",
                    model="gpt-5.2",
                    output_type=JurorTurn,
                    instructions=(
                        "You are Juror C (Pragmatist). Focus on practical interpretation and likely "
                        "intent. Input includes claim_text, claim_polarity, turn_index, and "
                        "prior_turns. Consider prior turns.\n"
                        "Also include reactions[] to prior turns (like/dislike) referencing juror_id "
                        "and turn_index."
                    ),
                )
            ),
            build_agent(
                AgentDefinition(
                    name="juror_historian",
                    model="gpt-5.2",
                    output_type=JurorTurn,
                    instructions=(
                        "You are Juror D (Historian). Provide historical context where relevant. "
                        "Input includes claim_text, claim_polarity, turn_index, and prior_turns. "
                        "Consider prior turns.\n"
                        "Also include reactions[] to prior turns (like/dislike) referencing juror_id "
                        "and turn_index."
                    ),
                )
            ),
            build_agent(
                AgentDefinition(
                    name="juror_contrarian",
                    model="gpt-5.2",
                    output_type=JurorTurn,
                    instructions=(
                        "You are Juror E (Contrarian). Stress-test the majority view and propose "
                        "alternative interpretations. Input includes claim_text, claim_polarity, "
                        "turn_index, and prior_turns. Consider prior turns.\n"
                        "Also include reactions[] to prior turns (like/dislike) referencing juror_id "
                        "and turn_index."
                    ),
                )
            ),
        ],
    )
