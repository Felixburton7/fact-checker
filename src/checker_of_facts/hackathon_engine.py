"""
Hackathon Debate Engine for Cambridge DIS Hackathon.

Implements the multi-agent jury debate with:
- Random juror order per round
- 2 rounds (each juror speaks twice)
- Moderator summary after round 1
- Final verdict after round 2
- Real-time printing of debate output
"""
from __future__ import annotations

import asyncio
import json
import random
from dataclasses import asdict, is_dataclass
from typing import Any, Awaitable, Protocol
from datetime import datetime, timezone

from checker_of_facts.hackathon_models import (
    ClaimTruthPair,
    DebateRound,
    DebateResult,
    DebateTurn,
    ModeratorFinalVerdict,
    ModeratorSummary,
    JurorPersona,
    DEFAULT_JUROR_PERSONAS,
)
from checker_of_facts.hackathon_agents import (
    HackathonAgentRegistry,
    build_hackathon_registry,
)

try:
    from agents import Agent, Runner
except Exception:  # pragma: no cover - soft dependency
    Agent = None
    Runner = None


# ANSI color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


# Color mapping for jurors
JUROR_COLORS = {
    "skeptic": Colors.RED,
    "pedant": Colors.BLUE,
    "pragmatist": Colors.GREEN,
    "devil_advocate": Colors.YELLOW,
    "context_expert": Colors.CYAN,
}


class RunnerProtocol(Protocol):
    def run(
        self,
        starting_agent: "Agent",
        input: str,
        *,
        max_turns: int = 10,
    ) -> Awaitable[object]:
        raise NotImplementedError


def _to_jsonable(value: object) -> object:
    """Convert dataclasses and nested structures to JSON-serializable format."""
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.END}\n")


def print_claim_truth(pair: ClaimTruthPair) -> None:
    """Print the claim and truth being debated."""
    print(f"{Colors.BOLD}📋 INTERNAL FACT (Ground Truth):{Colors.END}")
    print(f"   {pair.truth}\n")
    print(f"{Colors.BOLD}🔍 EXTERNAL CLAIM (Under Review):{Colors.END}")
    print(f"   {pair.claim}\n")


def print_debate_turn(turn: DebateTurn) -> None:
    """Print a single debate turn with formatting."""
    color = JUROR_COLORS.get(turn.persona, Colors.END)
    print(f"{color}{Colors.BOLD}🎭 {turn.juror_name} ({turn.persona}){Colors.END}")
    print(f"{color}   Round {turn.round_number}, Turn {turn.turn_index}{Colors.END}")
    print(f"   {turn.content}")
    print()


def print_moderator_summary(summary: ModeratorSummary) -> None:
    """Print the moderator's mid-debate summary."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}⚖️  MODERATOR SUMMARY (After Round 1){Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'─' * 60}{Colors.END}\n")
    
    print(f"{Colors.BOLD}Summary:{Colors.END}")
    print(f"   {summary.summary}\n")
    
    print(f"{Colors.BOLD}Key Points:{Colors.END}")
    for point in summary.key_points:
        print(f"   • {point}")
    print()
    
    print(f"{Colors.BOLD}Areas of Agreement:{Colors.END}")
    for area in summary.areas_of_agreement:
        print(f"   ✓ {area}")
    print()
    
    print(f"{Colors.BOLD}Areas of Disagreement:{Colors.END}")
    for area in summary.areas_of_disagreement:
        print(f"   ✗ {area}")
    print()
    
    print(f"{Colors.BOLD}Guidance for Round 2:{Colors.END}")
    print(f"   {summary.guidance_for_next_round}")
    print()


def print_final_verdict(verdict: ModeratorFinalVerdict) -> None:
    """Print the final judge's verdict."""
    print(f"\n{Colors.BOLD}{'═' * 60}{Colors.END}")
    print(f"{Colors.BOLD}👨‍⚖️  FINAL JUDGE - VERDICT{Colors.END}")
    print(f"{Colors.BOLD}{'═' * 60}{Colors.END}\n")
    
    # Verdict label with color
    if verdict.label == "Faithful":
        label_color = Colors.GREEN
        emoji = "✅"
    elif verdict.label == "Mutated":
        label_color = Colors.RED
        emoji = "❌"
    else:
        label_color = Colors.YELLOW
        emoji = "❓"
    
    print(f"{label_color}{Colors.BOLD}{emoji} VERDICT: {verdict.label}{Colors.END}")
    print(f"{Colors.BOLD}   Confidence: {verdict.confidence:.0%}{Colors.END}\n")
    
    print(f"{Colors.BOLD}Summary:{Colors.END}")
    print(f"   {verdict.summary}\n")
    
    print(f"{Colors.BOLD}Rationale:{Colors.END}")
    for bullet in verdict.rationale_bullets:
        print(f"   • {bullet}")
    print()
    
    print(f"{Colors.BOLD}{Colors.GREEN}Arguments for 'Faithful':{Colors.END}")
    for arg in verdict.key_arguments_for_faithful:
        print(f"   + {arg}")
    print()
    
    print(f"{Colors.BOLD}{Colors.RED}Arguments for 'Mutated':{Colors.END}")
    for arg in verdict.key_arguments_for_mutated:
        print(f"   - {arg}")
    print()
    
    print(f"{Colors.BOLD}Final Reasoning:{Colors.END}")
    print(f"   {verdict.final_reasoning}")
    print()


class HackathonDebateEngine:
    """Engine for running multi-round jury debates."""
    
    def __init__(
        self,
        registry: HackathonAgentRegistry | None = None,
        runner: RunnerProtocol | None = None,
        personas: list[JurorPersona] | None = None,
        model: str = "gpt-5.2",
        verbose: bool = True,
    ):
        self.model = model
        self.personas = personas or DEFAULT_JUROR_PERSONAS
        self.registry = registry or build_hackathon_registry(self.personas, model)
        self.runner = runner or self._default_runner()
        self.verbose = verbose
    
    def _default_runner(self) -> RunnerProtocol:
        if Runner is None:
            raise RuntimeError("OpenAI Agents SDK is not installed.")
        return Runner
    
    def run(self, pair: ClaimTruthPair) -> DebateResult:
        """Run a complete debate on a claim/truth pair."""
        return asyncio.run(self._run_async(pair))
    
    async def _run_async(self, pair: ClaimTruthPair) -> DebateResult:
        """Async implementation of the debate."""
        if self.verbose:
            print_header("JURY DEBATE SESSION")
            print_claim_truth(pair)
        
        # Get juror IDs
        juror_ids = list(self.registry.jurors.keys())
        
        # ═══════════════════════════════════════════════════════════
        # ROUND 1: First iteration with random order
        # ═══════════════════════════════════════════════════════════
        round1_order = juror_ids.copy()
        random.shuffle(round1_order)
        
        if self.verbose:
            print_header("ROUND 1")
            print(f"Speaking order: {', '.join(round1_order)}\n")
        
        round1_turns: list[DebateTurn] = []
        for turn_idx, juror_id in enumerate(round1_order, 1):
            turn = await self._run_juror_turn(
                pair=pair,
                juror_id=juror_id,
                round_number=1,
                turn_index=turn_idx,
                prior_turns=round1_turns,
            )
            round1_turns.append(turn)
            
            if self.verbose:
                print_debate_turn(turn)
        
        round1 = DebateRound(
            round_number=1,
            juror_order=round1_order,
            turns=round1_turns,
        )
        
        # ═══════════════════════════════════════════════════════════
        # MODERATOR SUMMARY: Summarize round 1 and set tone for round 2
        # ═══════════════════════════════════════════════════════════
        moderator_summary = await self._run_moderator_summary(pair, round1_turns)
        
        if self.verbose:
            print_moderator_summary(moderator_summary)
        
        # ═══════════════════════════════════════════════════════════
        # ROUND 2: Second iteration with new random order
        # ═══════════════════════════════════════════════════════════
        round2_order = juror_ids.copy()
        random.shuffle(round2_order)
        
        if self.verbose:
            print_header("ROUND 2")
            print(f"Speaking order: {', '.join(round2_order)}\n")
        
        # Include all prior context for round 2
        all_prior_turns = round1_turns.copy()
        round2_turns: list[DebateTurn] = []
        
        for turn_idx, juror_id in enumerate(round2_order, 1):
            turn = await self._run_juror_turn(
                pair=pair,
                juror_id=juror_id,
                round_number=2,
                turn_index=turn_idx,
                prior_turns=all_prior_turns + round2_turns,
                moderator_summary=moderator_summary,
            )
            round2_turns.append(turn)
            
            if self.verbose:
                print_debate_turn(turn)
        
        round2 = DebateRound(
            round_number=2,
            juror_order=round2_order,
            turns=round2_turns,
        )
        
        # ═══════════════════════════════════════════════════════════
        # FINAL VERDICT: Final Judge delivers conclusion
        # ═══════════════════════════════════════════════════════════
        final_verdict = await self._run_final_judge_verdict(
            pair=pair,
            all_turns=round1_turns + round2_turns,
            moderator_summary=moderator_summary,
        )
        
        if self.verbose:
            print_final_verdict(final_verdict)
        
        return DebateResult(
            pair=pair,
            rounds=[round1, round2],
            moderator_summary=moderator_summary,
            final_verdict=final_verdict,
        )
    
    async def _run_juror_turn(
        self,
        pair: ClaimTruthPair,
        juror_id: str,
        round_number: int,
        turn_index: int,
        prior_turns: list[DebateTurn],
        moderator_summary: ModeratorSummary | None = None,
    ) -> DebateTurn:
        """Run a single juror's turn in the debate."""
        agent = self.registry.jurors[juror_id]
        persona = next(p for p in self.personas if p.id == juror_id)
        
        # Build input for the agent
        input_data = {
            "internal_fact": pair.truth,
            "external_claim": pair.claim,
            "juror_id": juror_id,
            "juror_name": persona.name,
            "persona": persona.persona,
            "round_number": round_number,
            "turn_index": turn_index,
            "prior_turns": [_to_jsonable(t) for t in prior_turns],
        }
        
        if moderator_summary:
            input_data["moderator_summary"] = _to_jsonable(moderator_summary)
        
        result = await self.runner.run(
            agent,
            json.dumps(input_data),
            max_turns=4,
        )
        
        output = result.final_output
        
        # Handle case where output is already a DebateTurn or needs conversion
        if isinstance(output, DebateTurn):
            return output
        elif hasattr(output, 'content'):
            return DebateTurn(
                juror_id=juror_id,
                juror_name=persona.name,
                persona=persona.persona,
                round_number=round_number,
                turn_index=turn_index,
                content=output.content,
            )
        else:
            # Fallback: treat output as the content string
            return DebateTurn(
                juror_id=juror_id,
                juror_name=persona.name,
                persona=persona.persona,
                round_number=round_number,
                turn_index=turn_index,
                content=str(output),
            )
    
    async def _run_moderator_summary(
        self,
        pair: ClaimTruthPair,
        round1_turns: list[DebateTurn],
    ) -> ModeratorSummary:
        """Run the moderator summary after round 1."""
        input_data = {
            "internal_fact": pair.truth,
            "external_claim": pair.claim,
            "round_1_turns": [_to_jsonable(t) for t in round1_turns],
        }
        
        result = await self.runner.run(
            self.registry.moderator,
            json.dumps(input_data),
            max_turns=4,
        )
        
        output = result.final_output
        
        if isinstance(output, ModeratorSummary):
            return output
        else:
            # Fallback parsing
            return ModeratorSummary(
                summary=str(output),
                key_points=[],
                areas_of_agreement=[],
                areas_of_disagreement=[],
                guidance_for_next_round="Continue debating.",
            )
    
    async def _run_final_judge_verdict(
        self,
        pair: ClaimTruthPair,
        all_turns: list[DebateTurn],
        moderator_summary: ModeratorSummary,
    ) -> ModeratorFinalVerdict:
        """Run the final judge to deliver the verdict."""
        input_data = {
            "internal_fact": pair.truth,
            "external_claim": pair.claim,
            "all_debate_turns": [_to_jsonable(t) for t in all_turns],
            "moderator_summary": _to_jsonable(moderator_summary),
        }
        
        result = await self.runner.run(
            self.registry.final_judge,
            json.dumps(input_data),
            max_turns=4,
        )
        
        output = result.final_output
        
        if isinstance(output, ModeratorFinalVerdict):
            return output
        else:
            # Fallback
            return ModeratorFinalVerdict(
                label="Unclear",
                confidence=0.5,
                summary=str(output),
                rationale_bullets=[],
                key_arguments_for_faithful=[],
                key_arguments_for_mutated=[],
                final_reasoning="Unable to parse verdict.",
            )
