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
