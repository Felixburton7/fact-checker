from dataclasses import dataclass
from datetime import datetime, timezone
from checker_of_facts.agents.sdk import AgentRegistry
from checker_of_facts.engine import EngineFactory
from checker_of_facts.mcp.workspace import FileWorkspace
from checker_of_facts.models import (
    ClaimAtom,
    ClaimBundle,
    CriticResult,
    EvidenceItem,
    EvidencePack,
    JudgeVerdict,
    ManagerDirective,
    RetrievalQueryBundle,
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
        manager=FakeAgent("manager"),
        claim=FakeAgent("claim_agent"),
        planner=FakeAgent("retrieval_planner"),
        collectors={
            "gov_stats": FakeAgent("gov_stats_collector"),
            "news": FakeAgent("news_collector"),
        },
        critic=FakeAgent("critic"),
        judges={
            "strict": FakeAgent("strict_judge"),
            "pragmatic": FakeAgent("pragmatic_judge"),
            "skeptical": FakeAgent("skeptical_judge"),
        },
    )


def test_empty_evidence_returns_not_enough(tmp_path):
    workspace = FileWorkspace(tmp_path)
    outputs = {
        "manager": ManagerDirective(
            source_mix_requirement="Tier A + Tier B", require_citations=True
        ),
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
        "retrieval_planner": [
            RetrievalQueryBundle(
                claim_id="claim_1",
                exact_phrase='"The Moon is made of cheese."',
                entity_predicate="Moon",
                timeframe_query=None,
                debunk_query="fact check The Moon is made of cheese.",
                source_mix_requirement="Tier A + Tier B",
            )
        ],
        "gov_stats_collector": EvidencePack(
            claim_atom_id="claim_1", collector_name="gov_stats", items=[]
        ),
        "news_collector": EvidencePack(claim_atom_id="claim_1", collector_name="news", items=[]),
        "critic": CriticResult(claim_id="claim_1", ranked_items=[], flags=[], coverage_gaps=[]),
        "strict_judge": JudgeVerdict(
            claim_id="claim_1",
            judge_id="strict",
            label="NotEnoughEvidence",
            confidence=0.2,
            rationale_bullets=["No evidence collected."],
            cited_evidence_ids=[],
            missing_evidence=["Need allowlisted sources with direct quotes."],
        ),
        "pragmatic_judge": JudgeVerdict(
            claim_id="claim_1",
            judge_id="pragmatic",
            label="NotEnoughEvidence",
            confidence=0.2,
            rationale_bullets=["No evidence collected."],
            cited_evidence_ids=[],
            missing_evidence=["Need allowlisted sources with direct quotes."],
        ),
        "skeptical_judge": JudgeVerdict(
            claim_id="claim_1",
            judge_id="skeptical",
            label="NotEnoughEvidence",
            confidence=0.2,
            rationale_bullets=["No evidence collected."],
            cited_evidence_ids=[],
            missing_evidence=["Need allowlisted sources with direct quotes."],
        ),
    }
    engine = EngineFactory(
        workspace=workspace,
        runner=FakeRunner(outputs),
        agent_registry=build_fake_registry(),
    ).build()

    result = engine.run("The Moon is made of cheese.")

    assert result.claims
    assert result.claims[0].final_verdict.label == "NotEnoughEvidence"
    assert result.claims[0].final_verdict.cited_evidence_ids == []


def test_report_schema_keys(tmp_path):
    workspace = FileWorkspace(tmp_path)
    now = datetime.now(timezone.utc).isoformat()
    evidence_item = EvidenceItem(
        id="claim_1_gov_stats_1",
        url="https://allowed.com/article",
        domain="allowed.com",
        tier="A",
        title="Evidence",
        published_at="2024-01-01",
        retrieved_at=now,
        quote="Quoted evidence.",
        context=None,
        hash="hash",
        source_profile="gov_stats",
    )
    outputs = {
        "manager": ManagerDirective(
            source_mix_requirement="Tier A + Tier B", require_citations=True
        ),
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
        "retrieval_planner": [
            RetrievalQueryBundle(
                claim_id="claim_1",
                exact_phrase='"Test claim."',
                entity_predicate="Test",
                timeframe_query=None,
                debunk_query="fact check Test claim.",
                source_mix_requirement="Tier A + Tier B",
            )
        ],
        "gov_stats_collector": EvidencePack(
            claim_atom_id="claim_1", collector_name="gov_stats", items=[evidence_item]
        ),
        "news_collector": EvidencePack(
            claim_atom_id="claim_1", collector_name="news", items=[]
        ),
        "critic": CriticResult(
            claim_id="claim_1", ranked_items=[evidence_item], flags=[], coverage_gaps=[]
        ),
        "strict_judge": JudgeVerdict(
            claim_id="claim_1",
            judge_id="strict",
            label="Supported",
            confidence=0.7,
            rationale_bullets=["Tier A evidence supports the claim. (cites: claim_1_gov_stats_1)"],
            cited_evidence_ids=["claim_1_gov_stats_1"],
            missing_evidence=[],
        ),
        "pragmatic_judge": JudgeVerdict(
            claim_id="claim_1",
            judge_id="pragmatic",
            label="Supported",
            confidence=0.6,
            rationale_bullets=["Multiple sources support the claim. (cites: claim_1_gov_stats_1)"],
            cited_evidence_ids=["claim_1_gov_stats_1"],
            missing_evidence=[],
        ),
        "skeptical_judge": JudgeVerdict(
            claim_id="claim_1",
            judge_id="skeptical",
            label="NotEnoughEvidence",
            confidence=0.35,
            rationale_bullets=["Need more Tier A evidence."],
            cited_evidence_ids=["claim_1_gov_stats_1"],
            missing_evidence=["Need more Tier A evidence across multiple domains."],
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
    assert claim_result.final_verdict.cited_evidence_ids

