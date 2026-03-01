"""Doc and code retrieval: chunk content and return only sections relevant to the ticket."""

import re
from typing import Sequence

# Max total characters of doc chunks to include in context (avoids token overflow)
MAX_RETRIEVED_DOC_CHARS = 6000
# Max total characters of code chunks for bug RCA/fix (keeps context bounded)
MAX_RETRIEVED_CODE_CHARS = 10_000

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
    scored = [((h, b), _score_chunk(f"{h}\n{b}", terms)) for h, b in chunks]
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


# ---- Code retrieval (bug path) ----

def chunk_code_by_files_and_symbols(code_text: str) -> list[tuple[str, str]]:
    """
    Split code_context into chunks: by file, then by top-level def/class within file.
    Returns list of (file_header, block_content) e.g. ("--- store.py ---", "def add_snippet(...)...")
    """
    if not code_text or not code_text.strip():
        return []
    # Split by file header: "--- filename ---" (at start or after newline)
    file_parts = re.split(r"(?:^|\n)---\s+([^\n]+?)\s+---\n", code_text.strip())
    if len(file_parts) < 2:
        if code_text.strip():
            return [("", code_text.strip())]
        return []
    chunks: list[tuple[str, str]] = []
    # file_parts[0] is content before first header (often empty); then [name1, content1, name2, content2, ...]
    i = 1
    while i + 1 < len(file_parts):
        name, content = file_parts[i], file_parts[i + 1]
        header = f"--- {name.strip()} ---"
        content = content.strip()
        if not content:
            i += 2
            continue
        # Sub-split by top-level def/class (at start of line) so we can retrieve single functions
        symbol_blocks = re.split(r"^(?=def |class )", content, flags=re.MULTILINE)
        if len(symbol_blocks) <= 1:
            chunks.append((header, content))
        else:
            for block in symbol_blocks:
                block = block.strip()
                if block:
                    chunks.append((header, block))
        i += 2
    return chunks


def get_search_queries_for_bug(ticket: str, *, llm_callback=None) -> list[str]:
    """
    Get search phrases for code retrieval (bug path): file names, function names, error terms.
    Uses LLM if callback provided for better relevance.
    """
    if llm_callback:
        try:
            prompt = (
                "A user reported a bug. We will search source code to find the cause.\n\n"
                f"Bug report: {ticket}\n\n"
                "List 4 to 8 short phrases or identifiers to search for in the code: "
                "file or module names (e.g. store, main), function/variable names, error messages, or keywords. "
                "One per line, no numbering. Only output the phrases."
            )
            raw = (llm_callback(prompt) or "").strip()
            if raw:
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                phrases = [
                    ln for ln in lines[:12]
                    if not ln.lower().startswith("here are") and len(ln) < 60
                ][:8]
                if phrases:
                    return phrases
        except Exception:
            pass
    return _extract_search_terms_fallback(ticket)


def _score_code_chunk(chunk_text: str, file_header: str, query_terms: Sequence[str]) -> int:
    """Score a code chunk by query term matches; boost if term matches filename."""
    combined = f"{file_header}\n{chunk_text}".lower()
    score = sum(1 for q in query_terms if q.lower() in combined)
    # Boost for filename match (e.g. "store" in "--- store.py ---")
    file_lower = file_header.lower()
    for q in query_terms:
        ql = q.lower()
        if ql in file_lower and len(ql) > 1:
            score += 2
    return score


def retrieve_relevant_code(
    full_code: str,
    ticket: str,
    *,
    search_queries: list[str] | None = None,
    max_chars: int = MAX_RETRIEVED_CODE_CHARS,
) -> str:
    """
    Return only code chunks relevant to the bug report.
    Chunks are file-level or function/class-level; scored by keyword match and filename boost.
    """
    if not full_code or not full_code.strip():
        return ""
    chunks = chunk_code_by_files_and_symbols(full_code)
    if not chunks:
        return full_code[:max_chars]
    terms = search_queries or _extract_search_terms_fallback(ticket)
    if not terms:
        # No terms: include first files until limit
        out_parts: list[str] = []
        n = 0
        for header, body in chunks:
            block = f"{header}\n\n{body}" if header else body
            if n + len(block) > max_chars and out_parts:
                break
            out_parts.append(block)
            n += len(block)
        return "\n\n".join(out_parts) if out_parts else full_code[:max_chars]
    scored = [((h, b), _score_code_chunk(b, h, terms)) for h, b in chunks]
    scored.sort(key=lambda x: -x[1])
    # Group by file header so we output one section per file with its chosen blocks
    by_file: dict[str, list[str]] = {}
    n = 0
    for (header, body), _ in scored:
        if n >= max_chars and by_file:
            break
        key = header or "(no file)"
        if key not in by_file:
            by_file[key] = []
        by_file[key].append(body)
        n += len(header) + len(body) + 4
    out_parts = []
    for header, bodies in by_file.items():
        if header == "(no file)":
            out_parts.append("\n\n".join(bodies))
        else:
            out_parts.append(f"{header}\n\n" + "\n\n".join(bodies))
    return "\n\n".join(out_parts) if out_parts else full_code[:max_chars]
