"""Ticket classification: heuristic fallback or LLM. Returns one of QUESTION, CONFUSION, BUG."""

import sys

from modules.langraph.config import has_anthropic_key
from modules.langraph.llm import call_claude
from modules.langraph.state import BUG, CLASSIFICATION_LABELS, CONFUSION, QUESTION


def heuristic_classify(ticket: str) -> str:
    """Classify when LLM is unavailable."""
    t = ticket.lower()
    if any(w in t for w in ("crash", "error", "doesn't work", "does not work", "bug", "broken")):
        return BUG
    if any(w in t for w in ("can't find", "don't understand", "how do i", "where do i", "confused")):
        return CONFUSION
    return QUESTION


def classify(ticket: str) -> str:
    """Classify ticket as question, confusion, or bug. Uses LLM if key set, else heuristic."""
    if not has_anthropic_key():
        return heuristic_classify(ticket)

    prompt = f"""Classify this support ticket into exactly one category:

- "{QUESTION}": The user is asking a factual question (e.g. "What is X?", "How many Y?").
- "{CONFUSION}": The user is confused about how to use the product (e.g. "I don't understand how to...", "Where do I find...?").
- "{BUG}": The user reports an actual bug or malfunction (e.g. "It crashes when...", "Error message...", "Feature X doesn't work").

Ticket:
---
{ticket}
---

Respond with ONLY one word: {QUESTION}, {CONFUSION}, or {BUG}."""

    try:
        raw = call_claude(prompt).strip().lower()
        return next((c for c in CLASSIFICATION_LABELS if c in raw), QUESTION)
    except Exception as e:
        print(f"[classify fallback] {type(e).__name__}: {e}", file=sys.stderr)
        return heuristic_classify(ticket)
