from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from checker_of_facts.config import DEFAULT_OPENAI_MODEL
from checker_of_facts.models import (
    ClaimBundle,
    CriticResult,
    EvidenceItem,
    EvidencePack,
    JudgeVerdict,
    ManagerDirective,
    RetrievalQueryBundle,
)

try:
    import agents
    from agents.mcp.server import MCPServer
except ImportError as exc:  # pragma: no cover - soft dependency
    agents = None
    MCPServer = None
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
    mcp_servers: list["MCPServer"] = field(default_factory=list)
    output_type: type[Any] | None = None


@dataclass(frozen=True)
class AgentRegistry:
    manager: AgentHandle
    claim: AgentHandle
    planner: AgentHandle
    collectors: dict[str, AgentHandle]
    critic: AgentHandle
    judges: dict[str, AgentHandle]


def build_agent(definition: AgentDefinition) -> AgentHandle:
    if agents is None:
        detail = f" ({_IMPORT_ERROR})" if _IMPORT_ERROR else ""
        raise RuntimeError(f"OpenAI Agents SDK is not installed{detail}.")
    return agents.Agent(
        name=definition.name,
        instructions=definition.instructions,
        model=definition.model,
        tools=definition.tools,
        mcp_servers=definition.mcp_servers,
        output_type=definition.output_type,
    )


def build_default_registry(
    model: str = DEFAULT_OPENAI_MODEL, mcp_servers: list["MCPServer"] | None = None
) -> AgentRegistry:
    mcp_servers = mcp_servers or []
    return AgentRegistry(
        manager=build_agent(
            AgentDefinition(
                name="manager",
                model=model,
                mcp_servers=mcp_servers,
                output_type=ManagerDirective,
                instructions=(
                    "You are the manager agent for a fact-check run. Your job is to establish the "
                    "run constraints and expectations before any evidence work begins.\n"
                    "Return a ManagerDirective JSON object with:\n"
                    "- source_mix_requirement: a short string describing the required tier mix\n"
                    "- require_citations: true if factual assertions must cite evidence\n"
                    "- notes: list of concise operational reminders\n"
                    "Rules:\n"
                    "- Never claim facts; only set policy directives.\n"
                    "- Default to 'Any tier (A-D), prefer A/B' if unsure.\n"
                    "- require_citations must be true.\n"
                ),
            )
        ),
        claim=build_agent(
            AgentDefinition(
                name="claim_agent",
                model=model,
                mcp_servers=mcp_servers,
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
        planner=build_agent(
            AgentDefinition(
                name="retrieval_planner",
                model=model,
                mcp_servers=mcp_servers,
                output_type=list[RetrievalQueryBundle],
                instructions=(
                    "You generate RetrievalQueryBundle entries for each claim. "
                    "Input includes a ClaimBundle and a ManagerDirective. For each claim, output:\n"
                    "- claim_id matching ClaimAtom.id\n"
                    "- exact_phrase: quoted claim text\n"
                    "- entity_predicate: entities joined or the claim text\n"
                    "- timeframe_query: include timeframe if present\n"
                    "- debunk_query: 'fact check {claim text}'\n"
                    "- source_mix_requirement: from ManagerDirective\n"
                    "Return a list ordered to match the claim list."
                ),
            )
        ),
        collectors={
            "gov_stats": build_agent(
                AgentDefinition(
                    name="gov_stats_collector",
                    model=model,
                    mcp_servers=mcp_servers,
                    output_type=EvidencePack,
                    instructions=(
                        "You collect government/statistical evidence using MCP tools. "
                        "You must:\n"
                        "1) Use at most 3 queries (prefer exact_phrase, entity_predicate, debunk_query).\n"
                        "2) Call retrieval_search with limit=5.\n"
                        "2) For each URL, call sources_normalize_url, sources_is_allowed_domain, "
                        "and sources_domain_tier. Skip disallowed domains.\n"
                        "3) Fetch at most 4 URLs total, aiming for distinct domains. Call "
                        "retrieval_fetch (or retrieval_fetch_pdf "
                        "for PDFs) and then "
                        "retrieval_extract_quotes (or retrieval_extract_pdf_quotes).\n"
                        "4) Build EvidenceItem entries with tier, canonical url, and quotes.\n"
                        "5) Call workspace_store_evidence_pack with the EvidencePack.\n"
                        "Notes:\n"
                        "- Accept Tier A/B/C/D evidence; prefer higher tiers.\n"
                        "- Extract up to 5 quotes per URL.\n"
                        "- Do not loop or retry once you've completed one pass.\n"
                        "If no results are found, return an EvidencePack with items: [].\n"
                        "Return the EvidencePack as your final response."
                    ),
                )
            ),
            "news": build_agent(
                AgentDefinition(
                    name="news_collector",
                    model=model,
                    mcp_servers=mcp_servers,
                    output_type=EvidencePack,
                    instructions=(
                        "You collect news evidence using MCP tools. "
                        "You must:\n"
                        "1) Use at most 3 queries (prefer exact_phrase, entity_predicate, debunk_query).\n"
                        "2) Call retrieval_search with limit=5.\n"
                        "2) For each URL, call sources_normalize_url, sources_is_allowed_domain, "
                        "and sources_domain_tier. Skip disallowed domains.\n"
                        "3) Fetch at most 4 URLs total, aiming for distinct domains. Call "
                        "retrieval_fetch (or retrieval_fetch_pdf "
                        "for PDFs) and then "
                        "retrieval_extract_quotes (or retrieval_extract_pdf_quotes).\n"
                        "4) Build EvidenceItem entries with tier, canonical url, and quotes.\n"
                        "5) Call workspace_store_evidence_pack with the EvidencePack.\n"
                        "Notes:\n"
                        "- Accept Tier A/B/C/D evidence; prefer higher tiers.\n"
                        "- Extract up to 5 quotes per URL.\n"
                        "- Do not loop or retry once you've completed one pass.\n"
                        "If no results are found, return an EvidencePack with items: [].\n"
                        "Return the EvidencePack as your final response."
                    ),
                )
            ),
        },
        critic=build_agent(
            AgentDefinition(
                name="critic",
                model=model,
                mcp_servers=mcp_servers,
                output_type=CriticResult,
                instructions=(
                    "You score evidence for a claim. Input includes claim_id and evidence items.\n"
                    "Output CriticResult with:\n"
                    "- claim_id\n"
                    "- ranked_items: evidence ordered by tier (A>B>C>D), then quote length\n"
                    "- flags: include missing_tier_a_b if no A/B evidence\n"
                    "- coverage_gaps: include no_evidence_found if items empty\n"
                    "Do not invent evidence."
                ),
            )
        ),
        judges={
            "strict": build_agent(
                AgentDefinition(
                    name="strict_judge",
                    model=model,
                    mcp_servers=mcp_servers,
                    output_type=JudgeVerdict,
                    instructions=(
                        "You are the strict judge. Input includes claim_text, claim_polarity, and "
                        "CriticResult.\n"
                        "Rules:\n"
                        "- If no evidence, label NotEnoughEvidence.\n"
                        "- Accept Tier A/B/C/D evidence; use lower confidence for C/D.\n"
                        "- Restate the claim in your own words and preserve negation; use "
                        "claim_polarity to avoid flipping the claim.\n"
                        "- Compare each evidence summary to the claim_text; if evidence contradicts "
                        "the claim, label Refuted.\n"
                        "- Treat 'current' or 'currently' as of the evidence retrieved_at date.\n"
                        "- If evidence is time-ambiguous or outdated for a 'current' claim, use "
                        "Mixed or NotEnoughEvidence.\n"
                        "- You may use prior knowledge to interpret evidence, but do not override "
                        "evidence or add uncited facts.\n"
                        "- Always list cited_evidence_ids for any Supported/Refuted/Mixed label.\n"
                        "- rationale_bullets must cite evidence ids when asserting facts.\n"
                        "- missing_evidence should describe what is needed if not enough.\n"
                        "Output JudgeVerdict with judge_id='strict'."
                    ),
                )
            ),
            "pragmatic": build_agent(
                AgentDefinition(
                    name="pragmatic_judge",
                    model=model,
                    mcp_servers=mcp_servers,
                    output_type=JudgeVerdict,
                    instructions=(
                        "You are the pragmatic judge. Input includes claim_text, claim_polarity, "
                        "and CriticResult.\n"
                        "Rules:\n"
                        "- If no evidence, label NotEnoughEvidence.\n"
                        "- Accept Tier A/B/C/D evidence; use lower confidence for C/D.\n"
                        "- Restate the claim in your own words and preserve negation; use "
                        "claim_polarity to avoid flipping the claim.\n"
                        "- Compare each evidence summary to the claim_text; if evidence contradicts "
                        "the claim, label Refuted.\n"
                        "- Treat 'current' or 'currently' as of the evidence retrieved_at date.\n"
                        "- If evidence is time-ambiguous or outdated for a 'current' claim, use "
                        "Mixed or NotEnoughEvidence.\n"
                        "- You may use prior knowledge to interpret evidence, but do not override "
                        "evidence or add uncited facts.\n"
                        "- Always list cited_evidence_ids for any Supported/Refuted/Mixed label.\n"
                        "- rationale_bullets must cite evidence ids when asserting facts.\n"
                        "- missing_evidence should describe what is needed if not enough.\n"
                        "Output JudgeVerdict with judge_id='pragmatic'."
                    ),
                )
            ),
            "skeptical": build_agent(
                AgentDefinition(
                    name="skeptical_judge",
                    model=model,
                    mcp_servers=mcp_servers,
                    output_type=JudgeVerdict,
                    instructions=(
                        "You are the skeptical judge. Input includes claim_text, claim_polarity, "
                        "and CriticResult.\n"
                        "Rules:\n"
                        "- If no evidence, label NotEnoughEvidence.\n"
                        "- Accept Tier A/B/C/D evidence; use lower confidence for C/D.\n"
                        "- Restate the claim in your own words and preserve negation; use "
                        "claim_polarity to avoid flipping the claim.\n"
                        "- Compare each evidence summary to the claim_text; if evidence contradicts "
                        "the claim, label Refuted.\n"
                        "- Treat 'current' or 'currently' as of the evidence retrieved_at date.\n"
                        "- If evidence is time-ambiguous or outdated for a 'current' claim, use "
                        "Mixed or NotEnoughEvidence.\n"
                        "- You may use prior knowledge to interpret evidence, but do not override "
                        "evidence or add uncited facts.\n"
                        "- Always list cited_evidence_ids for any Supported/Refuted/Mixed label.\n"
                        "- rationale_bullets must cite evidence ids when asserting facts.\n"
                        "- missing_evidence should describe what is needed if not enough.\n"
                        "Output JudgeVerdict with judge_id='skeptical'."
                    ),
                )
            ),
        },
    )
