from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse

import anyio
import httpx
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from checker_of_facts.config import BRAVE_API_KEY, TAVILY_API_KEY
from checker_of_facts.mcp.domain_registry import domain_tier, normalize_domain, normalize_url

try:  # Optional dependencies
    import trafilatura
    import trafilatura.metadata
except Exception:  # pragma: no cover
    trafilatura = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


server = Server(name="retrieval")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str | None
    snippet: str | None
    published_at: str | None
    source: str
    domain: str
    tier: str
    relevance: float
    canonical_url: str


def _normalize_search_url(url: str) -> str:
    parsed = urlparse(url)
    query_pairs = [
        (k, v)
        for k, v in [pair.split("=", 1) if "=" in pair else (pair, "") for pair in parsed.query.split("&") if pair]
        if not k.startswith("utm_")
    ]
    normalized_query = urlencode(query_pairs)
    return urlunparse(
        (
            parsed.scheme,
            normalize_domain(parsed.netloc),
            parsed.path,
            "",
            normalized_query,
            "",
        )
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _format_error_body(response: httpx.Response) -> str:
    try:
        data = response.json()
        payload = data if isinstance(data, dict) else {"data": data}
    except ValueError:
        payload = {"body": response.text}
    text = str(payload)
    return text[:1000]


def _raise_for_status_with_body(response: httpx.Response, label: str) -> None:
    if not response.is_error:
        return
    detail = _format_error_body(response)
    logger.warning("%s search failed (%s): %s", label, response.status_code, detail)
    raise httpx.HTTPStatusError(
        f"{label} search failed ({response.status_code}). Response: {detail}",
        request=response.request,
        response=response,
    )


async def _tavily_search(
    client: httpx.AsyncClient,
    query: str,
    max_results: int,
    freshness_days: int | None,
    include_domains: list[str] | None,
    exclude_domains: list[str] | None,
) -> list[SearchResult]:
    if not TAVILY_API_KEY:
        return []
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
    }
    if freshness_days is not None:
        payload["days"] = freshness_days
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains

    response = await client.post("https://api.tavily.com/search", json=payload, timeout=20)
    _raise_for_status_with_body(response, "Tavily")
    data = response.json()
    results = []
    for item in data.get("results", []):
        url = item.get("url")
        if not url:
            continue
        canonical = _normalize_search_url(url)
        _, domain = normalize_url(canonical)
        results.append(
            SearchResult(
                url=url,
                title=item.get("title"),
                snippet=item.get("content") or item.get("snippet"),
                published_at=item.get("published_date"),
                source="tavily",
                domain=domain,
                tier=domain_tier(domain),
                relevance=float(item.get("score") or 0.0),
                canonical_url=canonical,
            )
        )
    return results


async def _brave_search(
    client: httpx.AsyncClient,
    query: str,
    max_results: int,
    freshness_days: int | None,
    include_domains: list[str] | None,
    exclude_domains: list[str] | None,
) -> list[SearchResult]:
    if not BRAVE_API_KEY:
        return []
    params: dict[str, Any] = {"q": query, "count": max_results}
    if freshness_days is not None:
        params["freshness"] = f"pd:{freshness_days}d"
    response = await client.get(
        "https://api.search.brave.com/res/v1/web/search",
        params=params,
        headers={
            "X-Subscription-Token": BRAVE_API_KEY,
            "Accept": "application/json",
            "User-Agent": "checker-of-facts/0.1",
        },
        timeout=20,
    )
    _raise_for_status_with_body(response, "Brave")
    data = response.json()
    results = []
    for item in data.get("web", {}).get("results", []):
        url = item.get("url")
        if not url:
            continue
        canonical = _normalize_search_url(url)
        _, domain = normalize_url(canonical)
        results.append(
            SearchResult(
                url=url,
                title=item.get("title"),
                snippet=item.get("description"),
                published_at=item.get("age") or item.get("page_age"),
                source="brave",
                domain=domain,
                tier=domain_tier(domain),
                relevance=float(item.get("rank") or 0.0),
                canonical_url=canonical,
            )
        )
    return results


def _filter_domains(
    results: list[SearchResult],
    include_domains: list[str] | None,
    exclude_domains: list[str] | None,
) -> list[SearchResult]:
    if include_domains:
        include_set = {normalize_domain(domain) for domain in include_domains}
        results = [item for item in results if item.domain in include_set]
    if exclude_domains:
        exclude_set = {normalize_domain(domain) for domain in exclude_domains}
        results = [item for item in results if item.domain not in exclude_set]
    return results


def _rank_results(results: list[SearchResult]) -> list[SearchResult]:
    tier_weight = {"A": 4, "B": 3, "C": 2, "D": 1}

    def score(item: SearchResult) -> tuple[int, float, float]:
        tier_score = tier_weight.get(item.tier, 0)
        published = _parse_datetime(item.published_at)
        recency_score = published.timestamp() if published else 0.0
        return (tier_score, recency_score, item.relevance)

    return sorted(results, key=score, reverse=True)


def _dedupe(results: list[SearchResult]) -> list[SearchResult]:
    seen = set()
    deduped = []
    for item in results:
        if item.canonical_url in seen:
            continue
        seen.add(item.canonical_url)
        deduped.append(item)
    return deduped


async def _fetch_url(client: httpx.AsyncClient, url: str) -> tuple[str, str, bytes]:
    response = await client.get(url, timeout=30)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    return response.url.__str__(), content_type, response.content


def _extract_text_html(html: bytes) -> tuple[str, dict[str, str | None]]:
    decoded = html.decode("utf-8", errors="ignore")
    metadata = {"title": None, "author": None, "published_at": None, "canonical_url": None}
    if trafilatura is not None:
        extracted = trafilatura.extract(decoded) or ""
        meta = trafilatura.metadata.extract_metadata(decoded)
        if meta:
            metadata["title"] = meta.title
            metadata["author"] = meta.author
            metadata["published_at"] = meta.date
            metadata["canonical_url"] = meta.url
        return extracted, metadata
    stripped = re.sub(r"<[^>]+>", " ", decoded)
    return re.sub(r"\s+", " ", stripped).strip(), metadata


def _extract_text_pdf(pdf_bytes: bytes) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(pdf_bytes)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _extract_quotes_from_text(text: str, claim_text: str, max_quotes: int) -> list[dict[str, str]]:
    claim_terms = {term.lower() for term in re.findall(r"\w+", claim_text) if len(term) > 2}
    sentences = _split_sentences(text)
    scored = []
    for idx, sentence in enumerate(sentences, 1):
        words = set(re.findall(r"\w+", sentence.lower()))
        overlap = len(words & claim_terms)
        if overlap:
            scored.append((overlap, idx, sentence))
    scored.sort(reverse=True)
    quotes = []
    for _, idx, sentence in scored[:max_quotes]:
        quotes.append(
            {
                "quote": sentence[:300],
                "location": f"sentence:{idx}",
                "section": "body",
            }
        )
    return quotes


def _extract_quotes_from_pdf(text: str, claim_text: str, max_quotes: int) -> list[dict[str, str]]:
    quotes = _extract_quotes_from_text(text, claim_text, max_quotes)
    for quote in quotes:
        quote["section"] = "pdf"
    return quotes


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="retrieval_search",
            description="Search the web using Tavily and Brave, merged and ranked.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "freshness_days": {"type": "integer"},
                    "include_domains": {"type": "array", "items": {"type": "string"}},
                    "exclude_domains": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "canonical_url": {"type": "string"},
                                "domain": {"type": "string"},
                                "tier": {"type": "string"},
                                "title": {"type": "string"},
                                "snippet": {"type": "string"},
                                "published_at": {"type": "string"},
                                "source": {"type": "string"},
                                "relevance": {"type": "number"},
                            },
                            "required": ["url", "canonical_url", "domain", "tier", "source"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["results"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="retrieval_fetch",
            description="Fetch a URL and return cleaned text plus metadata.",
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "canonical_url": {"type": "string"},
                    "domain": {"type": "string"},
                    "content_type": {"type": "string"},
                    "title": {"type": "string"},
                    "author": {"type": "string"},
                    "published_at": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["url", "canonical_url", "domain", "content_type", "text"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="retrieval_extract_quotes",
            description="Extract short attributable quotes from text or URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url_or_text": {"type": "string"},
                    "claim_text": {"type": "string"},
                    "max_quotes": {"type": "integer"},
                },
                "required": ["url_or_text", "claim_text"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "quotes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "quote": {"type": "string"},
                                "location": {"type": "string"},
                                "section": {"type": "string"},
                            },
                            "required": ["quote", "location", "section"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["quotes"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="retrieval_fetch_pdf",
            description="Fetch a PDF URL and return extracted text plus metadata.",
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "domain": {"type": "string"},
                    "title": {"type": "string"},
                    "author": {"type": "string"},
                    "published_at": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["url", "domain", "text"],
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="retrieval_extract_pdf_quotes",
            description="Extract short attributable quotes from PDF text or URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url_or_text": {"type": "string"},
                    "claim_text": {"type": "string"},
                    "max_quotes": {"type": "integer"},
                },
                "required": ["url_or_text", "claim_text"],
                "additionalProperties": False,
            },
            outputSchema={
                "type": "object",
                "properties": {
                    "quotes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "quote": {"type": "string"},
                                "location": {"type": "string"},
                                "section": {"type": "string"},
                            },
                            "required": ["quote", "location", "section"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["quotes"],
                "additionalProperties": False,
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]):
    if name == "retrieval_search":
        query = arguments["query"]
        freshness_days = arguments.get("freshness_days")
        include_domains = arguments.get("include_domains")
        exclude_domains = arguments.get("exclude_domains")
        limit = int(arguments.get("limit") or 10)

        async with httpx.AsyncClient() as client:
            try:
                tavily_results = await _tavily_search(
                    client,
                    query,
                    limit,
                    freshness_days,
                    include_domains,
                    exclude_domains,
                )
            except httpx.HTTPStatusError:
                tavily_results = []

            brave_results = []
            if not tavily_results:
                try:
                    brave_results = await _brave_search(
                        client,
                        query,
                        limit,
                        freshness_days,
                        include_domains,
                        exclude_domains,
                    )
                except httpx.HTTPStatusError:
                    brave_results = []

        merged = _filter_domains(tavily_results + brave_results, include_domains, exclude_domains)
        ranked = _rank_results(_dedupe(merged))[:limit]
        return {
            "results": [
                {
                    "url": item.url,
                    "canonical_url": item.canonical_url,
                    "domain": item.domain,
                    "tier": item.tier,
                    "title": item.title or "",
                    "snippet": item.snippet or "",
                    "published_at": item.published_at or "",
                    "source": item.source,
                    "relevance": item.relevance,
                }
                for item in ranked
            ]
        }

    if name == "retrieval_fetch":
        url = arguments["url"]
        async with httpx.AsyncClient() as client:
            canonical_url, content_type, body = await _fetch_url(client, url)
        normalized_url, domain = normalize_url(canonical_url)
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            text = _extract_text_pdf(body)
            return {
                "url": url,
                "canonical_url": normalized_url,
                "domain": domain,
                "content_type": content_type,
                "title": "",
                "author": "",
                "published_at": "",
                "text": text,
            }
        text, meta = _extract_text_html(body)
        return {
            "url": url,
            "canonical_url": meta.get("canonical_url") or normalized_url,
            "domain": domain,
            "content_type": content_type,
            "title": meta.get("title") or "",
            "author": meta.get("author") or "",
            "published_at": meta.get("published_at") or "",
            "text": text,
        }

    if name == "retrieval_extract_quotes":
        url_or_text = arguments["url_or_text"]
        claim_text = arguments["claim_text"]
        max_quotes = int(arguments.get("max_quotes") or 3)
        text = url_or_text
        if url_or_text.startswith("http"):
            async with httpx.AsyncClient() as client:
                _, content_type, body = await _fetch_url(client, url_or_text)
            if "application/pdf" in content_type or url_or_text.lower().endswith(".pdf"):
                text = _extract_text_pdf(body)
            else:
                text, _ = _extract_text_html(body)
        return {"quotes": _extract_quotes_from_text(text, claim_text, max_quotes)}

    if name == "retrieval_fetch_pdf":
        url = arguments["url"]
        async with httpx.AsyncClient() as client:
            canonical_url, _, body = await _fetch_url(client, url)
        _, domain = normalize_url(canonical_url)
        return {
            "url": url,
            "domain": domain,
            "title": "",
            "author": "",
            "published_at": "",
            "text": _extract_text_pdf(body),
        }

    if name == "retrieval_extract_pdf_quotes":
        url_or_text = arguments["url_or_text"]
        claim_text = arguments["claim_text"]
        max_quotes = int(arguments.get("max_quotes") or 3)
        text = url_or_text
        if url_or_text.startswith("http"):
            async with httpx.AsyncClient() as client:
                _, _, body = await _fetch_url(client, url_or_text)
            text = _extract_text_pdf(body)
        return {"quotes": _extract_quotes_from_pdf(text, claim_text, max_quotes)}

    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    anyio.run(main)
