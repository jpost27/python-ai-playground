"""Graph node handlers: each takes TicketState, returns state update dict."""

from modules.langraph.classifier import classify
from modules.langraph.config import has_anthropic_key
from modules.langraph.llm import SUPPORT_AGENT_SYSTEM, call_claude
from modules.langraph.state import TicketState


def classify_ticket(state: TicketState) -> dict:
    """Set classification from ticket text."""
    return {"classification": classify(state["ticket"])}


def answer_question(state: TicketState) -> dict:
    """Answer a factual question."""
    if not has_anthropic_key():
        return {"response": "[Demo mode] Set ANTHROPIC_API_KEY to enable."}
    try:
        text = call_claude(
            f"Support ticket (answer this factual question): {state['ticket']}",
            system=SUPPORT_AGENT_SYSTEM,
        )
        return {"response": text or "I couldn't generate an answer."}
    except Exception:
        return {"response": "[Demo mode] LLM call failed. Check API key and model."}


def suggest_help(state: TicketState) -> dict:
    """Suggest steps or resources for confused users."""
    if not has_anthropic_key():
        return {"response": "[Demo mode] Set ANTHROPIC_API_KEY to enable."}
    try:
        text = call_claude(
            f"Support ticket (user is confused — suggest steps or where to look): {state['ticket']}",
            system=SUPPORT_AGENT_SYSTEM,
        )
        return {"response": text or "I couldn't generate suggestions."}
    except Exception as e:
        return {"response": f"[LLM call failed] {type(e).__name__}: {e}"}


def root_cause_analysis(state: TicketState) -> dict:
    """Placeholder: bug analysis to be implemented."""
    ticket_preview = state["ticket"][:100] + ("..." if len(state["ticket"]) > 100 else "")
    return {
        "response": f"[Root cause analysis — to be implemented]\nTicket (BUG): {ticket_preview}"
    }
