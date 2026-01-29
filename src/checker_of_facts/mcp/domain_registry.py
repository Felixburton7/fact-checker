from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

from checker_of_facts.models import SourceTier


@dataclass(frozen=True)
class DomainProfile:
    domain: str
    tier: SourceTier
    rationale: str
    aliases: tuple[str, ...] = ()


_REGISTRY: list[DomainProfile] = [
    DomainProfile(
        domain="gov.uk",
        tier="A",
        rationale="UK government primary source.",
        aliases=("www.gov.uk",),
    ),
    DomainProfile(
        domain="ons.gov.uk",
        tier="A",
        rationale="UK Office for National Statistics.",
    ),
    DomainProfile(
        domain="nhs.uk",
        tier="A",
        rationale="UK National Health Service.",
    ),
    DomainProfile(
        domain="who.int",
        tier="A",
        rationale="World Health Organization.",
    ),
    DomainProfile(
        domain="oecd.org",
        tier="A",
        rationale="OECD statistics and reports.",
    ),
    DomainProfile(
        domain="worldbank.org",
        tier="A",
        rationale="World Bank data and publications.",
    ),
    DomainProfile(
        domain="imf.org",
        tier="A",
        rationale="IMF data and reports.",
    ),
    DomainProfile(
        domain="un.org",
        tier="A",
        rationale="United Nations.",
        aliases=("data.un.org",),
    ),
    DomainProfile(
        domain="eurostat.europa.eu",
        tier="A",
        rationale="EU official statistics.",
    ),
    DomainProfile(
        domain="ec.europa.eu",
        tier="A",
        rationale="European Commission.",
    ),
    DomainProfile(
        domain="cdc.gov",
        tier="A",
        rationale="US Centers for Disease Control and Prevention.",
    ),
    DomainProfile(
        domain="fda.gov",
        tier="A",
        rationale="US Food and Drug Administration.",
    ),
    DomainProfile(
        domain="nih.gov",
        tier="A",
        rationale="US National Institutes of Health.",
    ),
    DomainProfile(
        domain="census.gov",
        tier="A",
        rationale="US Census Bureau.",
    ),
    DomainProfile(
        domain="bls.gov",
        tier="A",
        rationale="US Bureau of Labor Statistics.",
    ),
    DomainProfile(
        domain="bea.gov",
        tier="A",
        rationale="US Bureau of Economic Analysis.",
    ),
    DomainProfile(
        domain="sec.gov",
        tier="A",
        rationale="US Securities and Exchange Commission filings.",
    ),
    DomainProfile(
        domain="usgs.gov",
        tier="A",
        rationale="US Geological Survey.",
    ),
    DomainProfile(
        domain="noaa.gov",
        tier="A",
        rationale="US National Oceanic and Atmospheric Administration.",
    ),
    DomainProfile(
        domain="epa.gov",
        tier="A",
        rationale="US Environmental Protection Agency.",
    ),
    DomainProfile(
        domain="nasa.gov",
        tier="A",
        rationale="US National Aeronautics and Space Administration.",
    ),
    DomainProfile(
        domain="statcan.gc.ca",
        tier="A",
        rationale="Statistics Canada.",
    ),
    DomainProfile(
        domain="canada.ca",
        tier="A",
        rationale="Government of Canada.",
    ),
    DomainProfile(
        domain="abs.gov.au",
        tier="A",
        rationale="Australian Bureau of Statistics.",
    ),
    DomainProfile(
        domain="health.gov.au",
        tier="A",
        rationale="Australian Department of Health.",
    ),
    DomainProfile(
        domain="data.gov",
        tier="A",
        rationale="US government data portal.",
    ),
    DomainProfile(
        domain="pubmed.ncbi.nlm.nih.gov",
        tier="A",
        rationale="PubMed registry.",
    ),
    DomainProfile(
        domain="crossref.org",
        tier="A",
        rationale="Crossref metadata registry.",
    ),
    DomainProfile(
        domain="openalex.org",
        tier="A",
        rationale="OpenAlex scholarly registry.",
    ),
    DomainProfile(
        domain="reuters.com",
        tier="B",
        rationale="Global wire service.",
        aliases=("www.reuters.com",),
    ),
    DomainProfile(
        domain="apnews.com",
        tier="B",
        rationale="Associated Press.",
    ),
    DomainProfile(
        domain="bbc.co.uk",
        tier="B",
        rationale="BBC News.",
        aliases=("www.bbc.co.uk", "bbc.com", "www.bbc.com"),
    ),
    DomainProfile(
        domain="ft.com",
        tier="B",
        rationale="Financial Times.",
    ),
    DomainProfile(
        domain="economist.com",
        tier="B",
        rationale="The Economist.",
    ),
    DomainProfile(
        domain="wsj.com",
        tier="B",
        rationale="Wall Street Journal.",
    ),
    DomainProfile(
        domain="nytimes.com",
        tier="B",
        rationale="New York Times.",
    ),
    DomainProfile(
        domain="theguardian.com",
        tier="B",
        rationale="The Guardian.",
    ),
    DomainProfile(
        domain="bloomberg.com",
        tier="B",
        rationale="Bloomberg News.",
    ),
    DomainProfile(
        domain="cnbc.com",
        tier="B",
        rationale="CNBC.",
    ),
    DomainProfile(
        domain="washingtonpost.com",
        tier="B",
        rationale="Washington Post.",
    ),
    DomainProfile(
        domain="latimes.com",
        tier="B",
        rationale="Los Angeles Times.",
    ),
    DomainProfile(
        domain="aljazeera.com",
        tier="B",
        rationale="Al Jazeera English.",
    ),
    DomainProfile(
        domain="npr.org",
        tier="B",
        rationale="NPR.",
    ),
    DomainProfile(
        domain="pbs.org",
        tier="B",
        rationale="PBS.",
    ),
    DomainProfile(
        domain="cnn.com",
        tier="B",
        rationale="CNN.",
    ),
    DomainProfile(
        domain="nationalgeographic.com",
        tier="B",
        rationale="National Geographic editorial coverage.",
    ),
    DomainProfile(
        domain="scientificamerican.com",
        tier="B",
        rationale="Scientific American coverage.",
    ),
    DomainProfile(
        domain="nature.com",
        tier="B",
        rationale="Nature news and commentary.",
    ),
    DomainProfile(
        domain="sciencemag.org",
        tier="B",
        rationale="Science magazine news.",
    ),
    DomainProfile(
        domain="abcnews.go.com",
        tier="B",
        rationale="ABC News.",
    ),
    DomainProfile(
        domain="cbsnews.com",
        tier="B",
        rationale="CBS News.",
    ),
    DomainProfile(
        domain="nbcnews.com",
        tier="B",
        rationale="NBC News.",
    ),
    DomainProfile(
        domain="wikipedia.org",
        tier="C",
        rationale="Community-maintained reference.",
    ),
    DomainProfile(
        domain="britannica.com",
        tier="C",
        rationale="Editorial reference.",
    ),
    DomainProfile(
        domain="avma.org",
        tier="C",
        rationale="American Veterinary Medical Association.",
    ),
    DomainProfile(
        domain="aspca.org",
        tier="C",
        rationale="ASPCA animal welfare guidance.",
    ),
    DomainProfile(
        domain="akc.org",
        tier="C",
        rationale="American Kennel Club informational content.",
    ),
    DomainProfile(
        domain="rspca.org.uk",
        tier="C",
        rationale="RSPCA animal welfare guidance.",
    ),
    DomainProfile(
        domain="veterinarypartner.vin.com",
        tier="C",
        rationale="Veterinary information service.",
    ),
    DomainProfile(
        domain="vet.cornell.edu",
        tier="A",
        rationale="Cornell University College of Veterinary Medicine.",
    ),
    DomainProfile(
        domain="vetmed.ucdavis.edu",
        tier="A",
        rationale="UC Davis School of Veterinary Medicine.",
    ),
    DomainProfile(
        domain="purdue.edu",
        tier="A",
        rationale="Purdue University research.",
    ),
    DomainProfile(
        domain="ourworldindata.org",
        tier="C",
        rationale="Secondary compilation with citations.",
    ),
    DomainProfile(
        domain="statista.com",
        tier="C",
        rationale="Secondary aggregation.",
    ),
    DomainProfile(
        domain="facebook.com",
        tier="D",
        rationale="Social media, blocked.",
        aliases=("m.facebook.com",),
    ),
    DomainProfile(
        domain="x.com",
        tier="D",
        rationale="Social media, blocked.",
        aliases=("twitter.com", "www.twitter.com"),
    ),
    DomainProfile(
        domain="tiktok.com",
        tier="D",
        rationale="Social media, blocked.",
    ),
    DomainProfile(
        domain="reddit.com",
        tier="D",
        rationale="User-generated forum, blocked.",
    ),
    DomainProfile(
        domain="instagram.com",
        tier="D",
        rationale="Social media, blocked.",
    ),
]


def normalize_domain(domain: str) -> str:
    cleaned = domain.lower().strip()
    if cleaned.startswith("www."):
        cleaned = cleaned[4:]
    return cleaned


def normalize_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    domain = normalize_domain(parsed.netloc)
    normalized = parsed._replace(netloc=domain, fragment="").geturl()
    return normalized, domain


def _matches(domain: str, profile: DomainProfile) -> bool:
    domain = normalize_domain(domain)
    candidates = (profile.domain, *profile.aliases)
    for candidate in candidates:
        candidate = normalize_domain(candidate)
        if domain == candidate or domain.endswith(f".{candidate}"):
            return True
    return False


def find_profile(domain: str) -> DomainProfile | None:
    for profile in _REGISTRY:
        if _matches(domain, profile):
            return profile
    return None


def domain_tier(domain: str) -> SourceTier:
    profile = find_profile(domain)
    if profile is None:
        return "D"
    return profile.tier


def get_domain_profile(domain: str) -> dict[str, object]:
    profile = find_profile(domain)
    if profile is None:
        return {
            "domain": normalize_domain(domain),
            "tier": "D",
            "rationale": "Unknown domain",
            "aliases": [],
        }
    return {
        "domain": normalize_domain(profile.domain),
        "tier": profile.tier,
        "rationale": profile.rationale,
        "aliases": list(profile.aliases),
    }


def detect_duplicates(urls: Iterable[str]) -> list[dict[str, object]]:
    buckets: dict[str, list[str]] = {}
    for url in urls:
        normalized, _ = normalize_url(url)
        buckets.setdefault(normalized, []).append(url)
    return [
        {"canonical_url": canonical, "urls": originals}
        for canonical, originals in buckets.items()
        if len(originals) > 1
    ]
