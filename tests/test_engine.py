from dataclasses import dataclass

from checker_of_facts.agents.sdk import AgentRegistry
from checker_of_facts.engine import EngineFactory
from checker_of_facts.mcp.workspace import FileWorkspace
from checker_of_facts.models import (
    ClaimAtom,
    ClaimBundle,
    JurorReaction,
    JurorTurn,
    ModeratorVerdict,
)


@dataclass(frozen=True)
class FakeAgent:
    name: str


class FakeRunner:
    def __init__(self, outputs: dict[str, object]) -> None:
        self._outputs = outputs

    async def run(self, starting_agent, input, *, max_turns=10):
        _ = input
        _ = max_turns
        return type("Result", (), {"final_output": self._outputs[starting_agent.name]})()


def build_fake_registry() -> AgentRegistry:
    return AgentRegistry(
        claim=FakeAgent("claim_agent"),
        moderator=FakeAgent("moderator"),
        jurors=[
            FakeAgent("juror_analyst"),
            FakeAgent("juror_skeptic"),
            FakeAgent("juror_pragmatist"),
            FakeAgent("juror_historian"),
            FakeAgent("juror_contrarian"),
        ],
    )


def test_internal_knowledge_verdict(tmp_path):
    workspace = FileWorkspace(tmp_path)
    outputs = {
        "claim_agent": ClaimBundle(
            raw_text="The Moon is made of cheese.",
            claims=[
                ClaimAtom(
                    id="claim_1",
                    text="The Moon is made of cheese.",
                    type="other",
                    entities=["Moon"],
                    timeframe=None,
                    numeric_values=[],
                )
            ],
        ),
        "juror_analyst": JurorTurn(
            juror_id="juror_analyst",
            persona="Analyst",
            turn_index=1,
            content="Defines the claim and notes basic facts.",
            reactions=[],
        ),
        "juror_skeptic": JurorTurn(
            juror_id="juror_skeptic",
            persona="Skeptic",
            turn_index=2,
            content="Challenges the claim and notes uncertainty.",
            reactions=[
                JurorReaction(
                    target_juror_id="juror_analyst",
                    target_turn_index=1,
                    reaction="dislike",
                )
            ],
        ),
        "juror_pragmatist": JurorTurn(
            juror_id="juror_pragmatist",
            persona="Pragmatist",
            turn_index=3,
            content="Interprets the claim in practical terms.",
            reactions=[
                JurorReaction(
                    target_juror_id="juror_skeptic",
                    target_turn_index=2,
                    reaction="like",
                )
            ],
        ),
        "juror_historian": JurorTurn(
            juror_id="juror_historian",
            persona="Historian",
            turn_index=4,
            content="Adds historical context.",
            reactions=[],
        ),
        "juror_contrarian": JurorTurn(
            juror_id="juror_contrarian",
            persona="Contrarian",
            turn_index=5,
            content="Stress-tests the majority view.",
            reactions=[
                JurorReaction(
                    target_juror_id="juror_historian",
                    target_turn_index=4,
                    reaction="like",
                )
            ],
        ),
        "moderator": ModeratorVerdict(
            label="Refuted",
            confidence=0.7,
            rationale_bullets=["Consensus of debate indicates the claim is false."],
            minority_report=None,
        ),
    }
    engine = EngineFactory(
        workspace=workspace,
        runner=FakeRunner(outputs),
        agent_registry=build_fake_registry(),
    ).build()

    result = engine.run("The Moon is made of cheese.")

    assert result.claims
    assert result.claims[0].final_verdict.label == "Refuted"
    assert result.claims[0].final_verdict.cited_evidence_ids == []
    assert result.claims[0].debate


def test_report_schema_keys(tmp_path):
    workspace = FileWorkspace(tmp_path)
    outputs = {
        "claim_agent": ClaimBundle(
            raw_text="Test claim.",
            claims=[
                ClaimAtom(
                    id="claim_1",
                    text="Test claim.",
                    type="other",
                    entities=["Test"],
                    timeframe=None,
                    numeric_values=[],
                )
            ],
        ),
        "juror_analyst": JurorTurn(
            juror_id="juror_analyst",
            persona="Analyst",
            turn_index=1,
            content="Summarizes the claim.",
            reactions=[],
        ),
        "juror_skeptic": JurorTurn(
            juror_id="juror_skeptic",
            persona="Skeptic",
            turn_index=2,
            content="Notes ambiguity.",
            reactions=[
                JurorReaction(
                    target_juror_id="juror_analyst",
                    target_turn_index=1,
                    reaction="like",
                )
            ],
        ),
        "juror_pragmatist": JurorTurn(
            juror_id="juror_pragmatist",
            persona="Pragmatist",
            turn_index=3,
            content="Explains likely intent.",
            reactions=[],
        ),
        "juror_historian": JurorTurn(
            juror_id="juror_historian",
            persona="Historian",
            turn_index=4,
            content="Provides historical context.",
            reactions=[],
        ),
        "juror_contrarian": JurorTurn(
            juror_id="juror_contrarian",
            persona="Contrarian",
            turn_index=5,
            content="Provides counterpoint.",
            reactions=[
                JurorReaction(
                    target_juror_id="juror_pragmatist",
                    target_turn_index=3,
                    reaction="dislike",
                )
            ],
        ),
        "moderator": ModeratorVerdict(
            label="Supported",
            confidence=0.6,
            rationale_bullets=["Moderator accepts the claim."],
            minority_report=None,
        ),
    }
    engine = EngineFactory(
        workspace=workspace,
        runner=FakeRunner(outputs),
        agent_registry=build_fake_registry(),
    ).build()

    report = engine.run("Test claim.")

    assert report.run_id
    assert report.input.text == "Test claim."
    assert report.claims
    claim_result = report.claims[0]
    assert claim_result.claim.id
    assert claim_result.final_verdict.label
    assert claim_result.final_verdict.cited_evidence_ids == []
    assert claim_result.debate
