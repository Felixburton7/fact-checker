from __future__ import annotations

from dataclasses import asdict
from typing import Any

import anyio
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from checker_of_facts.config import WORKSPACE_DIR
from checker_of_facts.mcp.workspace import FileWorkspace
from checker_of_facts.models import EvidenceItem, EvidencePack


server = Server(name="workspace")
workspace = FileWorkspace(WORKSPACE_DIR)


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []
    for item in items:
        key = item.get("hash") or f"{item.get('url')}|{item.get('quote')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="workspace_store_evidence_pack",
            description="Store an EvidencePack for a claim.",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim_atom_id": {"type": "string"},
                    "collector_name": {"type": "string"},
                    "items": {"type": "array", "items": {"type": "object"}},
                    "notes": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["claim_atom_id", "collector_name", "items"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="workspace_get_evidence",
            description="Load an EvidencePack for a claim and optional collector.",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim_atom_id": {"type": "string"},
                    "collector_name": {"type": "string"},
                },
                "required": ["claim_atom_id"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"evidence": {"type": "array", "items": {"type": "object"}}},
                "required": ["evidence"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="workspace_log_event",
            description="Append a run event to the workspace log.",
            inputSchema={
                "type": "object",
                "properties": {"event": {"type": "object"}},
                "required": ["event"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="workspace_dedupe_evidence",
            description="Dedupe evidence items by hash or url+quote.",
            inputSchema={
                "type": "object",
                "properties": {"items": {"type": "array", "items": {"type": "object"}}},
                "required": ["items"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"items": {"type": "array", "items": {"type": "object"}}},
                "required": ["items"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="workspace_cache_get",
            description="Get a cached value.",
            inputSchema={
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"value": {}},
                "required": ["value"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="workspace_cache_set",
            description="Set a cached value.",
            inputSchema={
                "type": "object",
                "properties": {"key": {"type": "string"}, "value": {}},
                "required": ["key", "value"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"],
                "additionalProperties": False,
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]):
    if name == "workspace_store_evidence_pack":
        items = [
            EvidenceItem(
                id=item["id"],
                url=item["url"],
                domain=item["domain"],
                tier=item["tier"],
                title=item.get("title"),
                published_at=item.get("published_at"),
                retrieved_at=item["retrieved_at"],
                quote=item["quote"],
                context=item.get("context"),
                hash=item["hash"],
                source_profile=item["source_profile"],
            )
            for item in arguments["items"]
        ]
        pack = EvidencePack(
            claim_atom_id=arguments["claim_atom_id"],
            collector_name=arguments["collector_name"],
            items=items,
            notes=arguments.get("notes", []),
        )
        workspace.store_evidence_pack(pack)
        return {"ok": True}
    if name == "workspace_get_evidence":
        claim_atom_id = arguments["claim_atom_id"]
        collector_name = arguments.get("collector_name")
        if collector_name:
            pack = workspace.load_evidence_pack(claim_atom_id, collector_name)
            if pack is None:
                return {"evidence": []}
            return {"evidence": [asdict(pack)]}

        evidence = []
        evidence_dir = workspace._evidence_dir  # noqa: SLF001
        for path in evidence_dir.glob(f"{claim_atom_id}__*.json"):
            collector = path.stem.split("__", 1)[1]
            pack = workspace.load_evidence_pack(claim_atom_id, collector)
            if pack is not None:
                evidence.append(asdict(pack))
        return {"evidence": evidence}
    if name == "workspace_log_event":
        workspace.log_event(arguments["event"])
        return {"ok": True}
    if name == "workspace_dedupe_evidence":
        return {"items": _dedupe_items(arguments["items"])}
    if name == "workspace_cache_get":
        return {"value": workspace.cache_get(arguments["key"])}
    if name == "workspace_cache_set":
        workspace.cache_set(arguments["key"], arguments["value"])
        return {"ok": True}

    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    anyio.run(main)
