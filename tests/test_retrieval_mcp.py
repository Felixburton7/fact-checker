import asyncio
import os
from datetime import datetime, timezone

import pytest
import httpx

import checker_of_facts.mcp_servers.retrieval as retrieval


def _make_result(url: str, tier: str, source: str, published_at: str | None = None):
    canonical = retrieval._normalize_search_url(url)
    _, domain = retrieval.normalize_url(canonical)
    return retrieval.SearchResult(
        url=url,
        title="Title",
        snippet="Snippet",
        published_at=published_at,
        source=source,
        domain=domain,
        tier=tier,
        relevance=0.5,
        canonical_url=canonical,
    )


def test_retrieval_search_merges_and_dedupes(monkeypatch):
    async def fake_tavily(*args, **kwargs):
        return [
            _make_result(
                "https://example.com/a",
                "B",
                "tavily",
                datetime.now(timezone.utc).date().isoformat(),
            ),
            _make_result("https://example.com/dup", "B", "tavily"),
        ]

    async def fake_brave(*args, **kwargs):
        return [
            _make_result("https://example.org/b", "A", "brave"),
            _make_result("https://example.com/dup", "B", "brave"),
        ]

    monkeypatch.setattr(retrieval, "_tavily_search", fake_tavily)
    monkeypatch.setattr(retrieval, "_brave_search", fake_brave)

    result = asyncio.run(
        retrieval.call_tool(
            "retrieval_search",
            {"query": "cats are stronger than dogs", "limit": 5},
        )
    )

    urls = [item["url"] for item in result["results"]]
    assert "https://example.com/dup" in urls
    assert urls.count("https://example.com/dup") == 1
    assert urls[0] == "https://example.org/b"


@pytest.mark.integration
def test_real_web_search_prints_results():
    if not os.getenv("TAVILY_API_KEY") or not os.getenv("BRAVE_API_KEY"):
        pytest.skip("Requires TAVILY_API_KEY and BRAVE_API_KEY to run.")

    async def run_searches():
        async with httpx.AsyncClient() as client:
            tavily = None
            brave = None
            try:
                tavily = await retrieval._tavily_search(
                    client, "cats are stronger than dogs", 5, None, None, None
                )
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != 401:
                    raise
            brave = await retrieval._brave_search(
                client, "cats are stronger than dogs", 5, None, None, None
            )
            return tavily, brave

    tavily_results, brave_results = asyncio.run(run_searches())

    print("Top results:")
    if tavily_results is not None:
        for item in tavily_results:
            print(f"- tavily | {item.tier} | {item.domain} | {item.url}")
    if brave_results is not None:
        for item in brave_results:
            print(f"- brave | {item.tier} | {item.domain} | {item.url}")

    assert tavily_results is not None or brave_results is not None
