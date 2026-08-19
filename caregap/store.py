"""In-memory member repository (repository pattern) backing the API.

Loads a cohort of FHIR bundles (JSON files) once and answers lookups. Kept behind a
simple interface so the storage mechanism (files now, a DB later) can be swapped.
"""

from __future__ import annotations

import json
from pathlib import Path

from .fhir_loader import load_member
from .model import Member


class MemberStore:
    """Holds parsed members indexed by id."""

    def __init__(self, members: list[Member]) -> None:
        self._members = list(members)
        self._by_id = {m.id: m for m in members}

    @property
    def members(self) -> list[Member]:
        return list(self._members)

    def __len__(self) -> int:
        return len(self._members)

    def get(self, member_id: str) -> Member | None:
        return self._by_id.get(member_id)

    def ids(self) -> list[str]:
        return [m.id for m in self._members]

    @classmethod
    def from_bundle_dir(cls, directory: str | Path) -> "MemberStore":
        """Load every ``*.json`` FHIR bundle in ``directory`` (sorted by filename)."""
        path = Path(directory)
        members: list[Member] = []
        for file in sorted(path.glob("*.json")):
            with file.open("r", encoding="utf-8") as fh:
                bundle = json.load(fh)
            members.append(load_member(bundle))
        return cls(members)

    @classmethod
    def from_bundles(cls, bundles: list[dict]) -> "MemberStore":
        return cls([load_member(b) for b in bundles])
