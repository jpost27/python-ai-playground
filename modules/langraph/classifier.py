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


def classify(
    ticket: str,
    *,
    docs_context: str = "",
    code_context: str = "",
) -> str:
    """Classify ticket as question, confusion, or bug. Uses LLM if key set, else heuristic.
    When docs_context and/or code_context are provided, the model uses them to tell apart
    confusion (user doesn't know how) from bug (feature doesn't work as documented).
    """
    if not has_anthropic_key():
        return heuristic_classify(ticket)

    context_parts = []
    if (docs_context or "").strip():
        context_parts.append("--- Relevant documentation ---\n" + docs_context.strip())
    if (code_context or "").strip():
        context_parts.append("--- Relevant code ---\n" + code_context.strip())
    context_block = "\n\n".join(context_parts) if context_parts else ""

    prompt = f"""Classify this support ticket into exactly one category:

- "{QUESTION}": The user is asking a factual question (e.g. "What is X?", "How many Y?").
- "{CONFUSION}": The user is confused about how to use the product — they need guidance or directions (e.g. "I don't understand how to...", "Where do I find...?"). They are NOT saying something that should work is broken.
- "{BUG}": The user reports an actual bug or malfunction: something that should work (per docs or design) does not work, crashes, or behaves wrongly (e.g. "It crashes when...", "Error when I...", "Feature X doesn't work as expected", "I did the steps but it still fails").

Use the documentation and code context below to decide: if the user is describing a feature that the docs/code say should work but it does not, choose {BUG}. If they are just unsure how to do something, choose {CONFUSION}.
"""
    if context_block:
        prompt += f"""
{context_block}

---
"""
    prompt += f"""Ticket:
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
