from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import asyncio
import json
import os
import re
from typing import Awaitable, Protocol
from uuid import uuid4

from checker_of_facts.agents.sdk import AgentRegistry, build_default_registry
from checker_of_facts.mcp.workspace import WorkspaceClient
from checker_of_facts.models import (
    ClaimInput,
    ClaimResult,
    FactCheckReport,
    FinalVerdict,
    JurorTurn,
    ModeratorVerdict,
)
from typing import Any

try:
    from agents import Agent, Runner
except Exception:  # pragma: no cover - soft dependency
    Agent = None
    Runner = None


class RunnerProtocol(Protocol):
    def run(
        self,
        starting_agent: "Agent",
        input: str,
        *,
        max_turns: int = 10,
    ) -> Awaitable[object]:
        raise NotImplementedError


@dataclass(frozen=True)
class FactCheckEngine:
    registry: AgentRegistry | None
    runner: RunnerProtocol
    workspace: WorkspaceClient

    def run(self, claim_text: str) -> FactCheckReport:
        return asyncio.run(self._run_async(claim_text))

    async def _run_async(self, claim_text: str) -> FactCheckReport:
        run_id = uuid4().hex
        self.workspace.log_event({"event": "start", "claim_text": claim_text, "run_id": run_id})

        registry = self.registry or build_default_registry()
        return await self._run_with_registry(claim_text, registry, run_id)

    async def _run_with_registry(
        self,
        claim_text: str,
        registry: AgentRegistry,
        run_id: str,
    ) -> FactCheckReport:
        bundle = await self._run_agent(
            registry.claim,
            json.dumps({"claim_text": claim_text}),
            max_turns=3,
        )
        self.workspace.log_event({"event": "claims_built", "count": len(bundle.claims)})

        claim_results: list[ClaimResult] = []
        for claim in bundle.claims:
            debate: list[JurorTurn] = []
            for index, juror in enumerate(registry.jurors, 1):
                turn = await self._run_agent(
                    juror,
                    json.dumps(
                        _to_jsonable(
                            {
                                "juror_id": juror.name,
                                "claim_text": claim.text,
                                "claim_polarity": _claim_polarity(claim.text),
                                "turn_index": index,
                                "prior_turns": debate,
                            }
                        )
                    ),
                    max_turns=4,
                )
                debate.append(turn)

            moderator_verdict = await self._run_agent(
                registry.moderator,
                json.dumps(
                    _to_jsonable(
                        {
                            "claim_text": claim.text,
                            "claim_polarity": _claim_polarity(claim.text),
                            "debate": debate,
                        }
                    )
                ),
                max_turns=4,
            )
            aggregate = _final_from_moderator(moderator_verdict)
            claim_results.append(
                ClaimResult(
                    claim=claim,
                    debate=debate,
                    moderator_verdict=moderator_verdict,
                    final_verdict=aggregate,
                )
            )
            self.workspace.log_event(
                {
                    "event": "claim_verdict",
                    "claim_id": claim.id,
                    "label": aggregate.label,
                    "confidence": aggregate.confidence,
                }
            )

        summary = None
        if len(claim_results) > 1:
            summary = "Multiple claims evaluated."

        return FactCheckReport(
            run_id=run_id,
            input=ClaimInput(text=claim_text),
            claims=claim_results,
            overall_summary=summary,
        )

    async def _run_agent(
        self, agent: Agent, input_payload: str, max_turns: int = 6
    ) -> object:
        result = await self.runner.run(agent, input_payload, max_turns=max_turns)
        return result.final_output


@dataclass(frozen=True)
class EngineFactory:
    workspace: WorkspaceClient
    agent_registry: AgentRegistry | None = None
    runner: RunnerProtocol | None = None

    def build(self) -> FactCheckEngine:
        registry = self.agent_registry
        runner = self.runner or _default_runner()
        _ensure_api_key(runner)
        return FactCheckEngine(
            registry=registry,
            runner=runner,
            workspace=self.workspace,
        )


def _default_runner() -> RunnerProtocol:
    if Runner is None:
        raise RuntimeError("OpenAI Agents SDK is not installed.")
    return Runner


def _ensure_api_key(runner: RunnerProtocol) -> None:
    if runner is Runner and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY must be set to use the Agents SDK runner.")


def _to_jsonable(value: object) -> object:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


def _final_from_moderator(verdict: ModeratorVerdict) -> FinalVerdict:
    return FinalVerdict(
        label=verdict.label,
        confidence=round(verdict.confidence, 2),
        consensus_rationale=verdict.rationale_bullets,
        cited_evidence_ids=[],
        disagreements=None,
        minority_report=verdict.minority_report,
    )


def _claim_polarity(text: str) -> str:
    negation = re.search(
        r"\b(not|no|never|without|isn't|aren't|wasn't|weren't|don't|doesn't|didn't|cannot|can't|won't)\b",
        text,
        flags=re.IGNORECASE,
    )
    return "negated" if negation else "affirmed"
