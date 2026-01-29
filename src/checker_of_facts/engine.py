from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
import asyncio
import json
import os
import re
from statistics import mean
from typing import Awaitable, Protocol
from uuid import uuid4

from checker_of_facts.agents.sdk import AgentRegistry, build_default_registry
from checker_of_facts.mcp.servers import build_mcp_servers
from checker_of_facts.mcp.workspace import WorkspaceClient
from checker_of_facts.models import (
    ClaimInput,
    ClaimResult,
    FactCheckReport,
    FinalVerdict,
    JudgeVerdict,
)
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

try:
    from agents import Agent, Runner
    from agents.mcp import MCPServerManager
    from agents.exceptions import MaxTurnsExceeded
except Exception:  # pragma: no cover - soft dependency
    Agent = None
    Runner = None
    MCPServerManager = None
    MaxTurnsExceeded = None


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
    mcp_servers: list[object]
    runner: RunnerProtocol
    workspace: WorkspaceClient

    def run(self, claim_text: str) -> FactCheckReport:
        return asyncio.run(self._run_async(claim_text))

    async def _run_async(self, claim_text: str) -> FactCheckReport:
        run_id = uuid4().hex
        self.workspace.log_event({"event": "start", "claim_text": claim_text, "run_id": run_id})

        registry = self.registry
        if registry is None:
            if MCPServerManager is None:
                raise RuntimeError("OpenAI Agents SDK MCP support is not available.")
            async with MCPServerManager(
                self.mcp_servers, connect_in_parallel=True
            ) as manager:
                registry = build_default_registry(mcp_servers=manager.active_servers)
                report = await self._run_with_registry(
                    claim_text, registry, run_id, manager.active_servers
                )
        else:
            report = await self._run_with_registry(claim_text, registry, run_id, [])

        return report

    async def _run_with_registry(
        self,
        claim_text: str,
        registry: AgentRegistry,
        run_id: str,
        mcp_servers: list[object],
    ) -> FactCheckReport:
        manager_directive = await self._run_agent(
            registry.manager,
            json.dumps({"claim_text": claim_text}),
            max_turns=3,
        )
        bundle = await self._run_agent(
            registry.claim,
            json.dumps({"claim_text": claim_text}),
            max_turns=3,
        )
        self.workspace.log_event({"event": "claims_built", "count": len(bundle.claims)})

        query_bundles = await self._run_agent(
            registry.planner,
            json.dumps(
                _to_jsonable(
                    {
                        "claims": bundle.claims,
                        "manager_directive": manager_directive,
                    }
                )
            ),
            max_turns=4,
        )
        self.workspace.log_event({"event": "queries_planned", "count": len(query_bundles)})

        claim_results: list[ClaimResult] = []
        for claim in bundle.claims:
            qbundle = next(qb for qb in query_bundles if qb.claim_id == claim.id)
            evidence_items = []
            for collector_name, collector_agent in registry.collectors.items():
                queries = [qbundle.exact_phrase, qbundle.entity_predicate]
                if qbundle.timeframe_query:
                    queries.append(qbundle.timeframe_query)
                if qbundle.debunk_query:
                    queries.append(qbundle.debunk_query)
                max_turns = 18
                try:
                    pack = await self._run_agent(
                        collector_agent,
                        json.dumps(
                            _to_jsonable(
                                {
                                    "claim_id": claim.id,
                                    "claim_text": claim.text,
                                    "collector_name": collector_name,
                                    "source_profile": collector_name,
                                    "queries": queries,
                                }
                            )
                        ),
                        max_turns=max_turns,
                    )
                except Exception as exc:
                    if MaxTurnsExceeded is None or not isinstance(exc, MaxTurnsExceeded):
                        raise
                    self.workspace.log_event(
                        {
                            "event": "collector_max_turns_exceeded",
                            "claim_id": claim.id,
                            "collector": collector_name,
                            "max_turns": max_turns,
                        }
                    )
                    pack = _empty_pack(claim.id, collector_name)
                if not pack.items and mcp_servers:
                    pack = await _manual_collect(
                        claim_id=claim.id,
                        claim_text=claim.text,
                        collector_name=collector_name,
                        queries=queries,
                        mcp_servers=mcp_servers,
                    )
                evidence_items.extend(pack.items)

            if not evidence_items:
                self.workspace.log_event(
                    {"event": "no_evidence", "claim_id": claim.id, "queries": queries}
                )

            evidence_items = _consolidate_evidence(evidence_items, claim.id)

            critic_result = await self._run_agent(
                registry.critic,
                json.dumps(
                    _to_jsonable(
                        {
                            "claim_id": claim.id,
                            "evidence_items": evidence_items,
                        }
                    )
                ),
                max_turns=4,
            )

            judge_votes: list[JudgeVerdict] = []
            for judge_name, judge_agent in registry.judges.items():
                verdict = await self._run_agent(
                    judge_agent,
                    json.dumps(
                        _to_jsonable(
                            {
                                "judge": judge_name,
                                "claim_text": claim.text,
                                "claim_polarity": _claim_polarity(claim.text),
                                "critic_result": critic_result,
                            }
                        )
                    ),
                    max_turns=4,
                )
                judge_votes.append(verdict)
            aggregate = _aggregate_verdict(judge_votes)
            claim_results.append(
                ClaimResult(
                    claim=claim,
                    evidence=evidence_items,
                    judge_verdicts=judge_votes,
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
        mcp_servers = [] if registry is not None else build_mcp_servers()
        runner = self.runner or _default_runner()
        _ensure_api_key(runner)
        return FactCheckEngine(
            registry=registry,
            mcp_servers=mcp_servers,
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


def _aggregate_verdict(judge_votes: list[JudgeVerdict]) -> FinalVerdict:
    label_counts = Counter(vote.label for vote in judge_votes)
    label = label_counts.most_common(1)[0][0]
    confidence = mean(vote.confidence for vote in judge_votes)
    if len(label_counts) > 1:
        confidence *= 0.85

    citations = []
    for vote in judge_votes:
        for citation in vote.cited_evidence_ids:
            if citation not in citations:
                citations.append(citation)

    disagreements = []
    for vote in judge_votes:
        if vote.label != label:
            disagreements.append(f"{vote.judge_id}: {vote.label}")

    consensus_rationale = []
    if label in {"Supported", "Refuted", "Mixed"} and citations:
        consensus_rationale.append(f"Consensus based on evidence: {', '.join(citations)}.")
    elif label in {"Supported", "Refuted", "Mixed"}:
        label = "NotEnoughEvidence"
        confidence = min(confidence, 0.3)
        consensus_rationale.append("Missing citations; defaulted to NotEnoughEvidence.")
    else:
        consensus_rationale.append("Insufficient evidence to reach a verdict.")

    return FinalVerdict(
        label=label,
        confidence=round(confidence, 2),
        consensus_rationale=consensus_rationale,
        cited_evidence_ids=citations,
        disagreements=disagreements or None,
        minority_report=None,
    )


def _claim_polarity(text: str) -> str:
    negation = re.search(
        r"\b(not|no|never|without|isn't|aren't|wasn't|weren't|don't|doesn't|didn't|cannot|can't|won't)\b",
        text,
        flags=re.IGNORECASE,
    )
    return "negated" if negation else "affirmed"


def _consolidate_evidence(items: list[object], claim_id: str) -> list[dict[str, Any]]:
    if not items:
        return []
    tier_weight = {"A": 4, "B": 3, "C": 2, "D": 1}

    def to_dict(item: object) -> dict[str, Any]:
        if is_dataclass(item):
            return asdict(item)
        if isinstance(item, dict):
            return dict(item)
        return dict(getattr(item, "__dict__", {}))

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        data = to_dict(item)
        domain = str(data.get("domain") or "")
        if not domain:
            continue
        grouped.setdefault(domain, []).append(data)

    consolidated = []
    for index, (domain, group) in enumerate(grouped.items(), 1):
        def score(entry: dict[str, Any]) -> tuple[int, int]:
            tier = str(entry.get("tier") or "D")
            quote = str(entry.get("quote") or "")
            return (tier_weight.get(tier, 0), len(quote))

        base = sorted(group, key=score, reverse=True)[0]
        quotes = []
        for entry in group:
            quote = str(entry.get("quote") or "").strip()
            if quote and quote not in quotes:
                quotes.append(quote)
        summary = " ".join(quotes[:5]).strip()
        consolidated.append(
            {
                "id": f"{claim_id}_domain_{index}",
                "url": base.get("url") or "",
                "domain": domain,
                "quote": summary,
                "tier": base.get("tier") or "D",
                "title": base.get("title"),
                "published_at": base.get("published_at"),
                "retrieved_at": base.get("retrieved_at") or "",
                "context": f"Summary from {len(quotes[:5])} quotes.",
                "hash": sha256(f"{domain}|{summary}".encode("utf-8")).hexdigest(),
                "source_profile": base.get("source_profile") or "news",
            }
        )

    consolidated.sort(
        key=lambda item: (tier_weight.get(str(item.get("tier") or "D"), 0), item["domain"]),
        reverse=True,
    )
    return consolidated


async def _manual_collect(
    claim_id: str,
    claim_text: str,
    collector_name: str,
    queries: list[str],
    mcp_servers: list[object],
) -> object:
    server_map = {getattr(server, "name", ""): server for server in mcp_servers}
    retrieval = server_map.get("retrieval")
    sources = server_map.get("sources")
    workspace = server_map.get("workspace")
    if retrieval is None or sources is None:
        return _empty_pack(claim_id, collector_name)

    results: list[dict[str, Any]] = []
    for query in queries:
        data = await _call_mcp_tool(retrieval, "retrieval_search", {"query": query, "limit": 5})
        results.extend(data.get("results", []))

    seen = set()
    items = []
    seen_domains: set[str] = set()
    for idx, result in enumerate(results, 1):
        url = result.get("canonical_url") or result.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        normalized = await _call_mcp_tool(sources, "sources_normalize_url", {"url": url})
        domain = normalized.get("domain") or result.get("domain") or ""
        allowed = await _call_mcp_tool(
            sources, "sources_is_allowed_domain", {"domain": domain}
        )
        if not allowed.get("allowed"):
            continue
        tier_info = await _call_mcp_tool(sources, "sources_domain_tier", {"domain": domain})
        tier = tier_info.get("tier") or result.get("tier") or "D"
        if domain in seen_domains and len(seen_domains) >= 3:
            continue
        fetched = await _call_mcp_tool(retrieval, "retrieval_fetch", {"url": url})
        quotes = await _call_mcp_tool(
            retrieval,
            "retrieval_extract_quotes",
            {"url_or_text": fetched.get("text", ""), "claim_text": claim_text, "max_quotes": 5},
        )
        if quotes.get("quotes"):
            seen_domains.add(domain)
        for quote_idx, quote in enumerate(quotes.get("quotes", []), 1):
            evidence_id = f"{claim_id}_{collector_name}_{idx}_{quote_idx}"
            text = quote.get("quote", "")
            items.append(
                {
                    "id": evidence_id,
                    "url": fetched.get("canonical_url", url),
                    "domain": domain,
                    "quote": text,
                    "tier": tier,
                    "title": fetched.get("title"),
                    "published_at": fetched.get("published_at"),
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "context": quote.get("section"),
                    "hash": sha256(f"{url}|{text}".encode("utf-8")).hexdigest(),
                    "source_profile": collector_name,
                }
            )

    pack = {"claim_atom_id": claim_id, "collector_name": collector_name, "items": items, "notes": []}
    if workspace is not None:
        await _call_mcp_tool(workspace, "workspace_store_evidence_pack", pack)
    return _pack_from_items(claim_id, collector_name, items)


def _empty_pack(claim_id: str, collector_name: str) -> object:
    return _pack_from_items(claim_id, collector_name, [])


def _pack_from_items(
    claim_id: str, collector_name: str, items: list[dict[str, Any]]
) -> object:
    return type(
        "Pack",
        (),
        {"items": items, "claim_atom_id": claim_id, "collector_name": collector_name},
    )()


async def _call_mcp_tool(server: object, name: str, args: dict[str, Any]) -> dict[str, Any]:
    result = await server.call_tool(name, args)
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    return {}
