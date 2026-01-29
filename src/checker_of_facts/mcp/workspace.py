from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Protocol

from checker_of_facts.models import EvidenceItem, EvidencePack


class WorkspaceClient(Protocol):
    def cache_get(self, key: str) -> object | None:
        raise NotImplementedError

    def cache_set(self, key: str, value: object) -> None:
        raise NotImplementedError

    def log_event(self, event: dict[str, object]) -> None:
        raise NotImplementedError

    def store_evidence_pack(self, pack: EvidencePack) -> None:
        raise NotImplementedError

    def load_evidence_pack(self, claim_id: str, collector_name: str) -> EvidencePack | None:
        raise NotImplementedError


class FileWorkspace:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path = self.base_dir / "cache.json"
        self._events_path = self.base_dir / "events.jsonl"
        self._evidence_dir = self.base_dir / "evidence"
        self._evidence_dir.mkdir(parents=True, exist_ok=True)

    def cache_get(self, key: str) -> object | None:
        if not self._cache_path.exists():
            return None
        data = json.loads(self._cache_path.read_text(encoding="utf-8"))
        return data.get(key)

    def cache_set(self, key: str, value: object) -> None:
        data: dict[str, object] = {}
        if self._cache_path.exists():
            data = json.loads(self._cache_path.read_text(encoding="utf-8"))
        data[key] = value
        self._cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def log_event(self, event: dict[str, object]) -> None:
        with self._events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")

    def store_evidence_pack(self, pack: EvidencePack) -> None:
        path = self._evidence_dir / f"{pack.claim_atom_id}__{pack.collector_name}.json"
        path.write_text(json.dumps(asdict(pack), indent=2), encoding="utf-8")

    def load_evidence_pack(self, claim_id: str, collector_name: str) -> EvidencePack | None:
        path = self._evidence_dir / f"{claim_id}__{collector_name}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
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
            for item in data.get("items", [])
        ]
        return EvidencePack(
            claim_atom_id=data["claim_atom_id"],
            collector_name=data["collector_name"],
            items=items,
            notes=data.get("notes", []),
        )
