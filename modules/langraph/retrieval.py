"""Doc retrieval: chunk docs and return only sections relevant to the ticket."""

import re
from typing import Sequence

# Max total characters of doc chunks to include in context (avoids token overflow)
MAX_RETRIEVED_DOC_CHARS = 6000

# Stopwords for fallback keyword extraction (no LLM)
_STOP = frozenset(
    {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "can", "to", "of", "in", "for", "on",
        "with", "at", "by", "from", "as", "into", "or", "and", "it", "i", "me",
        "my", "we", "our", "you", "your", "he", "she", "they", "this", "that",
        "what", "which", "when", "where", "how", "why", "if", "than", "but",
    }
)


def chunk_docs_by_headers(doc_text: str) -> list[tuple[str, str]]:
    """Split markdown into chunks by ## and ###. Returns list of (heading, chunk_text)."""
    if not doc_text or not doc_text.strip():
        return []
    # Split on lines that are ## or ### headers (at start of line)
    parts = re.split(r"^(#{2,3}\s+.+)$", doc_text.strip(), flags=re.MULTILINE)
    chunks: list[tuple[str, str]] = []
    current_heading = ""
    current_body: list[str] = []
    for i, block in enumerate(parts):
        block = block.strip()
        if not block:
            continue
        if block.startswith("##"):
            if current_body and current_heading:
                chunks.append((current_heading, "\n".join(current_body)))
            current_heading = block
            current_body = []
        else:
            current_body.append(block)
    if current_heading or current_body:
        chunks.append((current_heading, "\n".join(current_body)))
    # If no headers matched, treat whole doc as one chunk
    if not chunks and doc_text.strip():
        chunks.append(("", doc_text.strip()))
    return chunks


def _score_chunk(chunk_text: str, query_terms: Sequence[str]) -> int:
    """Score a chunk by number of query term matches (case-insensitive)."""
    lower = chunk_text.lower()
    return sum(1 for q in query_terms if q.lower() in lower)


def _extract_search_terms_fallback(ticket: str) -> list[str]:
    """Extract significant words from ticket when LLM is not available."""
    words = re.findall(r"[a-zA-Z0-9]{2,}", ticket)
    return [w for w in words if w.lower() not in _STOP][:12]


def get_search_queries_from_ticket(ticket: str, *, llm_callback=None) -> list[str]:
    """Get 3–5 search phrases for doc retrieval. Uses LLM if callback provided."""
    if llm_callback:
        try:
            prompt = (
                "A user submitted this support ticket. We will search documentation by keywords.\n\n"
                f"Ticket: {ticket}\n\n"
                "List 3 to 5 short phrases or keywords to search for in the docs (e.g. 'file size', 'export PDF', 'upload limit'). "
                "One phrase per line, no numbering. Only output the phrases."
            )
            raw = (llm_callback(prompt) or "").strip()
            if raw:
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                # Take first 5 non-empty lines, filter out boilerplate
                phrases = [
                    ln for ln in lines[:8]
                    if not ln.lower().startswith("here are")
                    and len(ln) < 80
                ][:5]
                if phrases:
                    return phrases
        except Exception:
            pass
    return _extract_search_terms_fallback(ticket)


def retrieve_relevant_docs(
    full_docs: str,
    ticket: str,
    *,
    search_queries: list[str] | None = None,
    max_chars: int = MAX_RETRIEVED_DOC_CHARS,
) -> str:
    """
    Return only doc sections relevant to the ticket.
    Uses search_queries if provided; otherwise treats ticket words as terms.
    """
    if not full_docs or not full_docs.strip():
        return ""
    chunks = chunk_docs_by_headers(full_docs)
    if not chunks:
        return full_docs[:max_chars]
    terms = search_queries or _extract_search_terms_fallback(ticket)
    if not terms:
        # No terms: return first few chunks to stay under limit
        out: list[str] = []
        n = 0
        for heading, body in chunks:
            block = f"{heading}\n\n{body}" if heading else body
            if n + len(block) > max_chars:
                break
            out.append(block)
            n += len(block)
        return "\n\n".join(out) if out else full_docs[:max_chars]
    # Score and sort by relevance
    scored = [(c, _score_chunk(f"{h}\n{b}", terms)) for h, b in chunks]
    scored.sort(key=lambda x: -x[1])
    out = []
    n = 0
    for (heading, body), _ in scored:
        block = f"{heading}\n\n{body}" if heading else body
        if n + len(block) > max_chars and out:
            break
        out.append(block)
        n += len(block)
    return "\n\n".join(out) if out else full_docs[:max_chars]
