"""Graph node handlers: each takes TicketState, returns state update dict."""

from modules.langraph.classifier import classify
from modules.langraph.config import has_anthropic_key
from modules.langraph.llm import SUPPORT_AGENT_SYSTEM, call_claude
from modules.langraph.state import TicketState


def classify_ticket(state: TicketState) -> dict:
    """Set classification from ticket text."""
    return {"classification": classify(state["ticket"])}


def _prompt_with_docs(docs_context: str, ticket: str, instruction: str) -> str:
    """Build user prompt with optional product docs."""
    if docs_context and docs_context.strip():
        return (
            f"Use the following product documentation as context. {instruction}\n\n"
            "--- Documentation ---\n"
            f"{docs_context.strip()}\n"
            "--- End documentation ---\n\n"
            f"Support ticket: {ticket}"
        )
    return f"Support ticket (no documentation loaded): {ticket}"


def answer_question(state: TicketState) -> dict:
    """Answer a factual question using product docs when available."""
    if not has_anthropic_key():
        return {"response": "[Demo mode] Set ANTHROPIC_API_KEY to enable."}
    try:
        prompt = _prompt_with_docs(
            state.get("docs_context") or "",
            state["ticket"],
            "Answer this factual question based on the documentation when possible.",
        )
        text = call_claude(prompt, system=SUPPORT_AGENT_SYSTEM)
        return {"response": text or "I couldn't generate an answer."}
    except Exception:
        return {"response": "[Demo mode] LLM call failed. Check API key and model."}


def suggest_help(state: TicketState) -> dict:
    """Suggest steps or resources for confused users using product docs when available."""
    if not has_anthropic_key():
        return {"response": "[Demo mode] Set ANTHROPIC_API_KEY to enable."}
    try:
        prompt = _prompt_with_docs(
            state.get("docs_context") or "",
            state["ticket"],
            "The user is confused — suggest steps or where to look, using the documentation to clear things up.",
        )
        text = call_claude(prompt, system=SUPPORT_AGENT_SYSTEM)
        return {"response": text or "I couldn't generate suggestions."}
    except Exception as e:
        return {"response": f"[LLM call failed] {type(e).__name__}: {e}"}


def root_cause_analysis(state: TicketState) -> dict:
    """Placeholder: bug analysis to be implemented."""
    ticket_preview = state["ticket"][:100] + ("..." if len(state["ticket"]) > 100 else "")
    return {
        "response": f"[Root cause analysis — to be implemented]\nTicket (BUG): {ticket_preview}"
    }
