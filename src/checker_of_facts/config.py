from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
MCP_RETRIEVAL_URL = os.getenv("MCP_RETRIEVAL_URL")
MCP_SOURCES_URL = os.getenv("MCP_SOURCES_URL")
MCP_WORKSPACE_URL = os.getenv("MCP_WORKSPACE_URL")

MCP_RETRIEVAL_TOOLS = os.getenv("MCP_RETRIEVAL_TOOLS")
MCP_SOURCES_TOOLS = os.getenv("MCP_SOURCES_TOOLS")
MCP_WORKSPACE_TOOLS = os.getenv("MCP_WORKSPACE_TOOLS")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", ".workspace")
