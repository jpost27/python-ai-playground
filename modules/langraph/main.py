"""
LangGraph module — support ticket classifier POC.

Takes a support ticket and routes to:
- question → answer it
- confusion → suggest help
- bug → root cause analysis (placeholder for later)

Run: uv run python -m modules.langraph.main
Uses base deps (langgraph is already installed).
"""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

# Load .env from project root (works regardless of cwd when run as module)
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")


def load_anthropic_config() -> tuple[str | None, str]:
    """Load API key and model from env. Returns (api_key, model). Use this everywhere for consistency."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    return api_key, model


# --- State schema ---


class TicketState(TypedDict):
    ticket: str
    classification: str
    response: str


# --- Classification labels ---

QUESTION = "question"
CONFUSION = "confusion"
BUG = "bug"

CLASSIFICATION_LABELS: tuple[str, ...] = (QUESTION, CONFUSION, BUG)


def _call_claude(prompt: str) -> str:
    """Call Claude via raw anthropic SDK (bypasses LangChain)."""
    api_key, model = load_anthropic_config()
    if not api_key:
        return ""
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text if msg.content else ""


def _heuristic_classify(ticket: str) -> str:
    """Fallback classifier when LLM is unavailable."""
    t = ticket.lower()
    if any(w in t for w in ("crash", "error", "doesn't work", "does not work", "bug", "broken")):
        return BUG
    if any(w in t for w in ("can't find", "don't understand", "how do i", "where do i", "confused")):
        return CONFUSION
    return QUESTION


# --- Nodes ---


def classify_ticket(state: TicketState) -> dict:
    """Classify the ticket as question, confusion, or bug."""
    api_key, _ = load_anthropic_config()
    if not api_key:
        return {"classification": _heuristic_classify(state["ticket"])}

    try:
        prompt = f"""Classify this support ticket into exactly one category:

- "{QUESTION}": The user is asking a factual question (e.g. "What is X?", "How many Y?").
- "{CONFUSION}": The user is confused about how to use the product (e.g. "I don't understand how to...", "Where do I find...?").
- "{BUG}": The user reports an actual bug or malfunction (e.g. "It crashes when...", "Error message...", "Feature X doesn't work").

Ticket:
---
{state["ticket"]}
---

Respond with ONLY one word: {QUESTION}, {CONFUSION}, or {BUG}."""

        raw = _call_claude(prompt).strip().lower()
        classification = next((c for c in CLASSIFICATION_LABELS if c in raw), QUESTION)
        return {"classification": classification}
    except Exception as e:
        # Fall back to heuristic; log so user can debug if needed
        import sys
        print(f"[classify fallback] {type(e).__name__}: {e}", file=sys.stderr)
        return {"classification": _heuristic_classify(state["ticket"])}


def answer_question(state: TicketState) -> dict:
    """Answer a factual question."""
    api_key, _ = load_anthropic_config()
    if not api_key:
        return {"response": "[Demo mode] Would answer the question using LLM. Set ANTHROPIC_API_KEY to enable."}
    llm, HumanMessage = _get_llm()
    try:
        msg = llm.invoke([HumanMessage(content=f"The user asked: {state['ticket']}\nProvide a helpful, concise answer.")])
        return {"response": msg.content or "I couldn't generate an answer."}
    except Exception:
        return {"response": "[Demo mode] LLM call failed. Check your API key and model access."}


def suggest_help(state: TicketState) -> dict:
    """Suggest help for product confusion."""
    api_key, _ = load_anthropic_config()
    if not api_key:
        return {"response": "[Demo mode] Would suggest help/docs. Set ANTHROPIC_API_KEY to enable."}
    try:
        text = _call_claude(f"User is confused: {state['ticket']}\nSuggest helpful resources or steps.")
        return {"response": text or "I couldn't generate suggestions."}
    except Exception as e:
        return {"response": f"[LLM call failed] {type(e).__name__}: {e}"}


def root_cause_analysis(state: TicketState) -> dict:
    """Placeholder for bug root cause analysis (to be implemented later)."""
    return {
        "response": (
            "[Root cause analysis flow — to be implemented]\n"
            f"Ticket classified as BUG: {state['ticket'][:100]}..."
        )
    }


# --- Routing ---


def route_by_classification(state: TicketState) -> Literal["answer_question", "suggest_help", "root_cause_analysis"]:
    """Route to the appropriate handler based on classification."""
    c = state.get("classification", QUESTION)
    if c == QUESTION:
        return "answer_question"
    if c == CONFUSION:
        return "suggest_help"
    return "root_cause_analysis"


# --- Graph ---


def build_graph() -> StateGraph:
    builder = StateGraph(TicketState)

    builder.add_node("classify", classify_ticket)
    builder.add_node("answer_question", answer_question)
    builder.add_node("suggest_help", suggest_help)
    builder.add_node("root_cause_analysis", root_cause_analysis)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route_by_classification)
    builder.add_edge("answer_question", END)
    builder.add_edge("suggest_help", END)
    builder.add_edge("root_cause_analysis", END)

    return builder.compile()


def main() -> None:
    api_key, model = load_anthropic_config()
    if not api_key:
        print("ANTHROPIC_API_KEY not set — using demo mode (heuristic classifier, placeholder responses)")
        print("Add ANTHROPIC_API_KEY=sk-ant-... to .env in the project root.\n")
    else:
        print(f"ANTHROPIC_API_KEY loaded — using LLM (model: {model})\n")

    graph = build_graph()

    # Example tickets to try
    examples = [
        "What is the maximum file size I can upload?",
        "I can't find where to export my report to PDF. Can you help?",
        "The app crashes when I click Save on a form with more than 50 fields.",
    ]

    print("Support ticket classifier (LangGraph POC)\n" + "=" * 50)
    for i, ticket in enumerate(examples, 1):
        print(f"\n--- Example {i} ---")
        print(f"Ticket: {ticket}")
        result = graph.invoke({"ticket": ticket, "classification": "", "response": ""})
        print(f"Classification: {result['classification']}")
        print(f"Response: {result['response'][:200]}..." if len(result.get("response", "")) > 200 else f"Response: {result.get('response', '')}")


if __name__ == "__main__":
    main()
