"""
Support ticket classifier — LangGraph POC.

Routes tickets: question → answer, confusion → suggest help, bug → RCA → propose fix → create PR.
Uses example_project/docs/USER_DOCS.md and example_project source as context.
Set GITHUB_TOKEN to create pull requests for bug fixes. Run: uv run python -m modules.langraph.main
"""

from pathlib import Path

from modules.langraph.config import has_anthropic_key, load_anthropic_config
from modules.langraph.graph import build_graph

# Repo root (parent of modules/)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_USER_DOCS_PATH = _REPO_ROOT / "example_project" / "docs" / "USER_DOCS.md"
_EXAMPLE_PROJECT_DIR = _REPO_ROOT / "example_project"


def _load_docs_context() -> str:
    """Load example project user docs for question/confusion context."""
    if not _USER_DOCS_PATH.exists():
        return ""
    try:
        return _USER_DOCS_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def _load_code_context() -> str:
    """Load example_project Python source for bug RCA/fix context."""
    if not _EXAMPLE_PROJECT_DIR.is_dir():
        return ""
    parts: list[str] = []
    for path in sorted(_EXAMPLE_PROJECT_DIR.glob("*.py")):
        try:
            parts.append(f"--- {path.name} ---\n{path.read_text(encoding='utf-8')}")
        except OSError:
            pass
    return "\n\n".join(parts) if parts else ""


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
    code_context = _load_code_context()
    if docs_context:
        print("Loaded example_project/docs/USER_DOCS.md as context for question/confusion.\n")
    if code_context:
        print("Loaded example_project source as context for bug RCA/fix.\n")

    print("Support ticket classifier (LangGraph POC)\n" + "=" * 50)
    for i, ticket in enumerate(examples, 1):
        print(f"\n--- Example {i} ---")
        print(f"Ticket: {ticket}")
        result = graph.invoke({
            "ticket": ticket,
            "classification": "",
            "response": "",
            "docs_context": docs_context,
            "code_context": code_context,
        })
        print(f"Classification: {result['classification']}")
        response = result.get("response", "")
        print(f"Response: {response[:200]}..." if len(response) > 200 else f"Response: {response}")


if __name__ == "__main__":
    main()
