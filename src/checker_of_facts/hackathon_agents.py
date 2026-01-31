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
    moderator: AgentHandle  # Single moderator for summary and guidance
    final_judge: AgentHandle  # Separate judge for final verdict


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


def build_juror_agent(persona: JurorPersona, model: str = "gpt-5.2") -> AgentHandle:
    """Build a juror agent with a specific persona."""
    instructions = f"""You are {persona.name} in a lively fact-checking debate.

YOUR STYLE: {persona.description}

TASK: Judge if an EXTERNAL CLAIM faithfully represents an INTERNAL FACT.
- "Faithful" = accurate, no distortion
- "Mutated" = distorted, exaggerated, or missing key context

DEBATE RULES:
- Keep it short and punchy - 2-3 sentences max per point
- Be conversational, like you're chatting with colleagues
- React to what others said - agree, push back, build on ideas
- Stay in character but don't be verbose
- Call out specific words/numbers that matter

OUTPUT: One concise, impactful contribution (1-2 short paragraphs). Get to the point fast.
"""
    
    return build_agent(
        AgentDefinition(
            name=f"juror_{persona.id}",
            model=model,
            output_type=DebateTurn,
            instructions=instructions,
        )
    )


def build_moderator_agent(model: str = "gpt-5.2") -> AgentHandle:
    """Build the single Moderator agent for summaries and guidance."""
    instructions = """You are the Moderator of a fact-checking jury debate.

YOUR ROLE:
You facilitate the debate - summarizing discussions, highlighting key tensions, and guiding jurors toward productive dialogue. You do NOT deliver final verdicts.

WHEN CALLED:
You will be asked to summarize after Round 1 and can also provide guidance after Round 2 if needed.

INPUT YOU WILL RECEIVE:
- The internal fact (ground truth)
- The external claim being evaluated
- All debate turns so far
- The phase of debate (after round 1 or after round 2)

YOUR OUTPUT (ModeratorSummary):
1. summary: Concise recap of arguments so far
2. key_points: Main points raised by jurors
3. areas_of_agreement: Where jurors align
4. areas_of_disagreement: Where jurors clash
5. guidance_for_next_round: What to focus on next (or final observations if after round 2)

Be neutral, fair, and constructive. Your job is to structure the debate, not judge it.
"""
    
    return build_agent(
        AgentDefinition(
            name="moderator",
            model=model,
            output_type=ModeratorSummary,
            instructions=instructions,
        )
    )


def build_final_judge_agent(model: str = "gpt-5.2") -> AgentHandle:
    """Build the Final Judge agent for delivering the verdict."""
    instructions = """You are the Final Judge of a fact-checking jury debate.

YOUR ROLE:
You are separate from the Moderator. After the jury has debated and the Moderator has summarized, YOU deliver the final, authoritative verdict.

YOUR TASK:
Weigh all arguments from the debate and render a definitive judgment on whether the claim is faithful to the original fact.

INPUT YOU WILL RECEIVE:
- The internal fact (ground truth)
- The external claim being evaluated
- All debate turns from both rounds
- The Moderator's summary and observations

YOUR OUTPUT (ModeratorFinalVerdict):
1. label: "Faithful", "Mutated", or "Unclear"
2. confidence: 0.0 to 1.0 (your certainty level)
3. summary: Brief summary of your decision
4. rationale_bullets: 3-5 key reasons supporting your verdict
5. key_arguments_for_faithful: Strongest pro-faithful arguments from debate
6. key_arguments_for_mutated: Strongest pro-mutated arguments from debate
7. final_reasoning: Your detailed reasoning explaining the verdict

Be fair, thorough, and decisive. Consider all perspectives but ultimately render a clear judgment.
Your verdict is final and must be well-reasoned and defensible.
"""
    
    return build_agent(
        AgentDefinition(
            name="final_judge",
            model=model,
            output_type=ModeratorFinalVerdict,
            instructions=instructions,
        )
    )


def build_hackathon_registry(
    personas: list[JurorPersona] | None = None,
    model: str = "gpt-5.2",
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
        moderator=build_moderator_agent(model),
        final_judge=build_final_judge_agent(model),
    )
