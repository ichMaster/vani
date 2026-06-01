"""Local JSON implementation of the Repository (Versions 0-1, v2 P1).

Documents live at `{state_dir}/{doc_type}/{doc_id}.json`, UTF-8, one file per
document. Writes are atomic (write-temp-then-rename) so a crash never leaves a
half-written document. A `cipher` hook allows sensitive documents to be
encrypted at rest (refinement #1); it is None until wired up.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from src.state.repository import Document, Repository

# A migrator upgrades a raw document to the current schema_version on read.
Migrator = Callable[[str, Document], Document]


class Cipher(Protocol):
    """At-rest encryption hook for sensitive documents."""

    def encrypt(self, text: str) -> str: ...
    def decrypt(self, text: str) -> str: ...


class JsonStore(Repository):
    """A Repository backed by local JSON files."""

    def __init__(
        self,
        state_dir: str | Path = ".vani_state",
        *,
        cipher: Cipher | None = None,
        migrator: Migrator | None = None,
    ) -> None:
        self._root = Path(state_dir)
        self._cipher = cipher
        self._migrator = migrator

    def _path(self, doc_type: str, doc_id: str) -> Path:
        return self._root / doc_type / f"{doc_id}.json"

    def save(self, doc_type: str, doc_id: str, data: Document) -> None:
        path = self._path(doc_type, doc_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if self._cipher is not None:
            text = self._cipher.encrypt(text)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)  # atomic on the same filesystem

    def load(self, doc_type: str, doc_id: str) -> Document | None:
        path = self._path(doc_type, doc_id)
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        if self._cipher is not None:
            text = self._cipher.decrypt(text)
        data = json.loads(text)
        if self._migrator is not None:
            data = self._migrator(doc_type, data)
        return data

    def list_ids(self, doc_type: str) -> list[str]:
        directory = self._root / doc_type
        if not directory.exists():
            return []
        return sorted(p.stem for p in directory.glob("*.json"))

    def delete(self, doc_type: str, doc_id: str) -> bool:
        path = self._path(doc_type, doc_id)
        if path.exists():
            path.unlink()
            return True
        return False
