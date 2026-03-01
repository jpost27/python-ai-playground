"""Graph state and classification labels."""

from typing_extensions import TypedDict

# Classification labels (must match graph node names where used)
QUESTION = "question"
CONFUSION = "confusion"
BUG = "bug"

CLASSIFICATION_LABELS: tuple[str, ...] = (QUESTION, CONFUSION, BUG)


class TicketState(TypedDict, total=False):
    """State passed through the support-ticket graph."""

    ticket: str
    classification: str
    response: str
    docs_context: str  # User docs (e.g. USER_DOCS.md) for question/confusion answers
    code_context: str  # Example project source for bug RCA/fix (may be filtered by retrieve_code)
    full_code_context: str  # Unfiltered code for propose_fix so generated diff has correct line numbers
    docs_for_classify: str  # Relevant doc snippets for classification (set before classify)
    code_for_classify: str  # Relevant code snippets for classification (set before classify)
    rca_result: str  # Root cause analysis text (bug path)
    suggested_fix: str  # Unified diff or fix description (bug path)
    pr_url: str  # Created PR URL if any (bug path)
