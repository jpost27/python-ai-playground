"""
Simple JSON-file storage for snippets.
Snippets have id, title, body, and created timestamp.
"""

from pathlib import Path
import json
from datetime import datetime, timezone


def _store_path() -> Path:
    return Path.cwd() / ".snippets.json"


def _load() -> list[dict]:
    p = _store_path()
    if not p.exists():
        return []
    raw = p.read_text(encoding="utf-8")
    if not raw.strip():
        return []
    return json.loads(raw)


def _save(snippets: list[dict]) -> None:
    _store_path().write_text(json.dumps(snippets, indent=2), encoding="utf-8")


def add_snippet(title: str, body: str) -> dict:
    """Append a new snippet; returns the created snippet with id and created."""
    snippets = _load()
    next_id = max((s.get("id", 0) for s in snippets), default=0) + 1
    created = datetime.now(tz=timezone.utc).isoformat()
    snippet = {"id": next_id, "title": title, "body": body, "created": created}
    snippets.append(snippet)
    _save(snippets)
    return snippet


def list_snippets() -> list[dict]:
    """Return all snippets (newest first)."""
    snippets = _load()
    return sorted(snippets, key=lambda s: s.get("created", ""), reverse=True)


def get_snippet(snippet_id: int) -> dict | None:
    """Return one snippet by id or None."""
    for s in _load():
        if s.get("id") == snippet_id:
            return s
    return None


def delete_snippet(snippet_id: int) -> bool:
    """Remove snippet by id; returns True if found and removed."""
    snippets = _load()
    before = len(snippets)
    snippets = [s for s in snippets if s.get("id") != snippet_id]
    if len(snippets) < before:
        _save(snippets)
        return True
    return False
