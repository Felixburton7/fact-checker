from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Iterable

from agents.mcp import MCPServerManager
from agents.mcp.server import MCPServerSse, MCPServerStdio, MCPServerStreamableHttp
from agents.mcp.util import create_static_tool_filter

from checker_of_facts.config import (
    BRAVE_API_KEY,
    MCP_RETRIEVAL_TOOLS,
    MCP_RETRIEVAL_URL,
    MCP_SOURCES_TOOLS,
    MCP_SOURCES_URL,
    MCP_TRANSPORT,
    MCP_WORKSPACE_TOOLS,
    MCP_WORKSPACE_URL,
    TAVILY_API_KEY,
)


def _parse_tool_allowlist(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def _stdio_env() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", os.getcwd())
    return env


def build_mcp_servers() -> list[object]:
    if MCP_TRANSPORT == "stdio":
        if not TAVILY_API_KEY and not BRAVE_API_KEY:
            raise RuntimeError(
                "Set TAVILY_API_KEY or BRAVE_API_KEY to enable retrieval MCP searches."
            )
        return [
            MCPServerStdio(
                params={
                    "command": sys.executable,
                    "args": ["-m", "checker_of_facts.mcp_servers.retrieval"],
                    "env": _stdio_env(),
                },
                name="retrieval",
            ),
            MCPServerStdio(
                params={
                    "command": sys.executable,
                    "args": ["-m", "checker_of_facts.mcp_servers.sources"],
                    "env": _stdio_env(),
                },
                name="sources",
            ),
            MCPServerStdio(
                params={
                    "command": sys.executable,
                    "args": ["-m", "checker_of_facts.mcp_servers.workspace"],
                    "env": _stdio_env(),
                },
                name="workspace",
            ),
        ]

    if not MCP_RETRIEVAL_URL or not MCP_SOURCES_URL or not MCP_WORKSPACE_URL:
        raise RuntimeError(
            "MCP_RETRIEVAL_URL, MCP_SOURCES_URL, and MCP_WORKSPACE_URL must be set."
        )

    retrieval_filter = create_static_tool_filter(_parse_tool_allowlist(MCP_RETRIEVAL_TOOLS))
    sources_filter = create_static_tool_filter(_parse_tool_allowlist(MCP_SOURCES_TOOLS))
    workspace_filter = create_static_tool_filter(_parse_tool_allowlist(MCP_WORKSPACE_TOOLS))

    if MCP_TRANSPORT == "streamable_http":
        return [
            MCPServerStreamableHttp(
                params={"url": MCP_RETRIEVAL_URL},
                name="retrieval",
                tool_filter=retrieval_filter,
            ),
            MCPServerStreamableHttp(
                params={"url": MCP_SOURCES_URL},
                name="sources",
                tool_filter=sources_filter,
            ),
            MCPServerStreamableHttp(
                params={"url": MCP_WORKSPACE_URL},
                name="workspace",
                tool_filter=workspace_filter,
            ),
        ]

    return [
        MCPServerSse(
            params={"url": MCP_RETRIEVAL_URL},
            name="retrieval",
            tool_filter=retrieval_filter,
        ),
        MCPServerSse(
            params={"url": MCP_SOURCES_URL},
            name="sources",
            tool_filter=sources_filter,
        ),
        MCPServerSse(
            params={"url": MCP_WORKSPACE_URL},
            name="workspace",
            tool_filter=workspace_filter,
        ),
    ]


@dataclass
class MCPRuntime:
    manager: MCPServerManager

    def close(self) -> None:
        asyncio.run(self.manager.cleanup_all())


def connect_mcp_servers(servers: Iterable[object]) -> MCPRuntime:
    manager = MCPServerManager(list(servers))
    asyncio.run(manager.connect_all())
    return MCPRuntime(manager=manager)
