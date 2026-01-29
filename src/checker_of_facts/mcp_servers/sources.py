from __future__ import annotations

from typing import Any

import anyio
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from checker_of_facts.mcp.domain_registry import (
    detect_duplicates,
    domain_tier,
    get_domain_profile,
    normalize_domain,
    normalize_url,
)


server = Server(name="sources")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="sources_normalize_url",
            description="Normalize a URL and return canonical URL + domain.",
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"normalized_url": {"type": "string"}, "domain": {"type": "string"}},
                "required": ["normalized_url", "domain"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="sources_is_allowed_domain",
            description="Return true if a domain is allowed (tier A/B/C/D).",
            inputSchema={
                "type": "object",
                "properties": {"domain": {"type": "string"}},
                "required": ["domain"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"allowed": {"type": "boolean"}, "tier": {"type": "string"}},
                "required": ["allowed", "tier"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="sources_domain_tier",
            description="Return the tier for a domain (A/B/C/D).",
            inputSchema={
                "type": "object",
                "properties": {"domain": {"type": "string"}},
                "required": ["domain"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"tier": {"type": "string"}},
                "required": ["tier"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="sources_get_domain_profile",
            description="Return tier, rationale, and aliases for a domain.",
            inputSchema={
                "type": "object",
                "properties": {"domain": {"type": "string"}},
                "required": ["domain"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string"},
                    "tier": {"type": "string"},
                    "rationale": {"type": "string"},
                    "aliases": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["domain", "tier", "rationale", "aliases"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="sources_detect_duplicates",
            description="Detect duplicate URLs after normalization.",
            inputSchema={
                "type": "object",
                "properties": {"urls": {"type": "array", "items": {"type": "string"}}},
                "required": ["urls"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "duplicates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "canonical_url": {"type": "string"},
                                "urls": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["canonical_url", "urls"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["duplicates"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="sources_require_mix",
            description="Check whether evidence items satisfy a tier mix requirement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "evidence_items": {"type": "array", "items": {"type": "object"}},
                    "requirement_string": {"type": "string"},
                },
                "required": ["evidence_items", "requirement_string"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "present": {"type": "array", "items": {"type": "string"}},
                    "missing": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["ok", "present", "missing"],
                "additionalProperties": False,
            },
        ),
    ]


def _parse_required_tiers(requirement: str) -> list[str]:
    tiers = []
    for tier in ["A", "B", "C", "D"]:
        if tier in requirement:
            tiers.append(tier)
    return tiers


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]):
    if name == "sources_normalize_url":
        normalized_url, domain = normalize_url(arguments["url"])
        return {"normalized_url": normalized_url, "domain": domain}
    if name == "sources_is_allowed_domain":
        domain = normalize_domain(arguments["domain"])
        tier = domain_tier(domain)
        return {"allowed": tier in {"A", "B", "C", "D"}, "tier": tier}
    if name == "sources_domain_tier":
        domain = normalize_domain(arguments["domain"])
        return {"tier": domain_tier(domain)}
    if name == "sources_get_domain_profile":
        return get_domain_profile(arguments["domain"])
    if name == "sources_detect_duplicates":
        return {"duplicates": detect_duplicates(arguments["urls"])}
    if name == "sources_require_mix":
        required = _parse_required_tiers(arguments["requirement_string"])
        present = {
            str(item.get("tier") or item.get("source_tier"))
            for item in arguments["evidence_items"]
        }
        missing = [tier for tier in required if tier not in present]
        return {"ok": not missing, "present": sorted(present), "missing": missing}

    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    anyio.run(main)
