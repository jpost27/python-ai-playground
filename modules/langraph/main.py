"""
Support ticket classifier — LangGraph POC.

Routes tickets: question → answer, confusion → suggest help, bug → root cause (placeholder).
Uses example_project/docs/USER_DOCS.md as context when answering questions or clearing up confusion.
Run: uv run python -m modules.langraph.main
"""

from pathlib import Path

from modules.langraph.config import has_anthropic_key, load_anthropic_config
from modules.langraph.graph import build_graph

# Repo root (parent of modules/)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_USER_DOCS_PATH = _REPO_ROOT / "example_project" / "docs" / "USER_DOCS.md"


def _load_docs_context() -> str:
    """Load example project user docs for question/confusion context."""
    if not _USER_DOCS_PATH.exists():
        return ""
    try:
        return _USER_DOCS_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> None:
    _, model = load_anthropic_config()
    if not has_anthropic_key():
        print("ANTHROPIC_API_KEY not set — using demo mode (heuristic classifier, placeholder responses)")
        print("Add ANTHROPIC_API_KEY=sk-ant-... to .env in the project root.\n")
    else:
        print(f"ANTHROPIC_API_KEY loaded — using LLM (model: {model})\n")

    graph = build_graph()

    examples = [
        "What is the maximum file size I can upload?",
        "I can't find where to export my report to PDF. Can you help?",
        "The app crashes when I click Save on a form with more than 50 fields.",
    ]

    docs_context = _load_docs_context()
    if docs_context:
        print("Loaded example_project/docs/USER_DOCS.md as context for question/confusion.\n")

    print("Support ticket classifier (LangGraph POC)\n" + "=" * 50)
    for i, ticket in enumerate(examples, 1):
        print(f"\n--- Example {i} ---")
        print(f"Ticket: {ticket}")
        result = graph.invoke({
            "ticket": ticket,
            "classification": "",
            "response": "",
            "docs_context": docs_context,
        })
        print(f"Classification: {result['classification']}")
        response = result.get("response", "")
        print(f"Response: {response[:200]}..." if len(response) > 200 else f"Response: {response}")


if __name__ == "__main__":
    main()
