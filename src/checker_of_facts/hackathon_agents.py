"""
Agent definitions for the Cambridge DIS Hackathon jury debate system.

Creates personality-driven juror agents and moderator agents.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from checker_of_facts.config import DEFAULT_OPENAI_MODEL
from checker_of_facts.hackathon_models import (
    DebateTurn,
    ModeratorFinalVerdict,
    ModeratorSummary,
    JurorPersona,
    DEFAULT_JUROR_PERSONAS,
)

try:
    import agents
except ImportError as exc:  # pragma: no cover - soft dependency
    agents = None
    _IMPORT_ERROR = exc
else:
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
class HackathonAgentRegistry:
    """Registry of agents for the hackathon debate system."""
    jurors: dict[str, AgentHandle]  # juror_id -> agent
    moderator_summary: AgentHandle
    moderator_verdict: AgentHandle


def build_agent(definition: AgentDefinition) -> AgentHandle:
    """Build an agent from a definition."""
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


def build_juror_agent(persona: JurorPersona, model: str = DEFAULT_OPENAI_MODEL) -> AgentHandle:
    """Build a juror agent with a specific persona."""
    instructions = f"""You are {persona.name}, a juror in a fact-checking debate.

YOUR PERSONA:
{persona.description}

YOUR TASK:
You are evaluating whether an EXTERNAL CLAIM is a faithful representation of an INTERNAL FACT.
- "Faithful" means the claim accurately represents the fact without distortion.
- "Mutated" means the claim distorts, exaggerates, omits critical context, or misrepresents the fact.

INPUT YOU WILL RECEIVE:
- The internal fact (ground truth)
- The external claim being evaluated
- All previous debate turns (what other jurors have said)
- Your turn number and round number

YOUR OUTPUT:
Provide a clear, compelling argument from YOUR persona's perspective.
- Stay in character with your persona
- Reference and respond to what previous jurors have said
- Be specific about WHY you think the claim is faithful or mutated
- Highlight specific phrases, numbers, or context that support your view

Keep your response focused and impactful (2-4 paragraphs maximum).
"""
    
    return build_agent(
        AgentDefinition(
            name=f"juror_{persona.id}",
            model=model,
            output_type=DebateTurn,
            instructions=instructions,
        )
    )


def build_moderator_summary_agent(model: str = DEFAULT_OPENAI_MODEL) -> AgentHandle:
    """Build the moderator agent for mid-debate summaries."""
    instructions = """You are the Moderator of a fact-checking jury debate.

YOUR TASK:
After the first round of debate, you must summarize the discussion and set the tone for the next round.

INPUT YOU WILL RECEIVE:
- The internal fact (ground truth)
- The external claim being evaluated
- All turns from Round 1 of the debate

YOUR OUTPUT:
Provide a ModeratorSummary with:
1. A concise summary of the arguments made so far
2. Key points raised by the jurors
3. Areas where jurors agree
4. Areas where jurors disagree
5. Guidance for the next round - what should jurors focus on or address?

Be neutral and fair. Your job is to help structure the debate, not to take sides.
Keep the guidance constructive and specific.
"""
    
    return build_agent(
        AgentDefinition(
            name="moderator_summary",
            model=model,
            output_type=ModeratorSummary,
            instructions=instructions,
        )
    )


def build_moderator_verdict_agent(model: str = DEFAULT_OPENAI_MODEL) -> AgentHandle:
    """Build the moderator agent for final verdict."""
    instructions = """You are the Moderator of a fact-checking jury debate, delivering the FINAL VERDICT.

YOUR TASK:
After all debate rounds, you must weigh the arguments and deliver a final verdict.

INPUT YOU WILL RECEIVE:
- The internal fact (ground truth)
- The external claim being evaluated
- All debate turns from both rounds
- The mid-debate summary you provided

YOUR OUTPUT:
Provide a ModeratorFinalVerdict with:
1. label: "Faithful", "Mutated", or "Unclear"
2. confidence: 0.0 to 1.0 (how confident you are)
3. summary: A brief summary of your decision
4. rationale_bullets: 3-5 key reasons for your verdict
5. key_arguments_for_faithful: Best arguments made for "Faithful"
6. key_arguments_for_mutated: Best arguments made for "Mutated"
7. final_reasoning: Your detailed reasoning for the verdict

Be fair and consider all perspectives. Acknowledge dissenting views.
Your verdict should be well-reasoned and defensible.
"""
    
    return build_agent(
        AgentDefinition(
            name="moderator_verdict",
            model=model,
            output_type=ModeratorFinalVerdict,
            instructions=instructions,
        )
    )


def build_hackathon_registry(
    personas: list[JurorPersona] | None = None,
    model: str = DEFAULT_OPENAI_MODEL,
) -> HackathonAgentRegistry:
    """Build the complete agent registry for the hackathon."""
    if personas is None:
        personas = DEFAULT_JUROR_PERSONAS
    
    jurors = {
        persona.id: build_juror_agent(persona, model)
        for persona in personas
    }
    
    return HackathonAgentRegistry(
        jurors=jurors,
        moderator_summary=build_moderator_summary_agent(model),
        moderator_verdict=build_moderator_verdict_agent(model),
    )
