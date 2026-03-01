"""
Support ticket classifier — LangGraph POC.

Routes tickets: question → answer, confusion → suggest help, bug → RCA → propose fix → create PR.
Uses example_project/docs/USER_DOCS.md and example_project source as context.
Set GITHUB_TOKEN to create pull requests for bug fixes.

Usage:
  uv run python -m modules.langraph.main           # interactive: prompts for ticket
  uv run python -m modules.langraph.main example   # run built-in example tickets
"""

import argparse
import sys
from pathlib import Path

from modules.langraph.config import has_anthropic_key, load_anthropic_config
from modules.langraph.graph import build_graph

# Repo root (parent of modules/)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_USER_DOCS_PATH = _REPO_ROOT / "example_project" / "docs" / "USER_DOCS.md"
_EXAMPLE_PROJECT_DIR = _REPO_ROOT / "example_project"

_EXAMPLES = [
    "What is the maximum file size I can upload?",
    "I can't find where to export my report to PDF. Can you help?",
    "The app crashes when I click Save on a form with more than 50 fields.",
]

_MAX_RESPONSE_LENGTH = 2000


def _format_step_value(key: str, value: str) -> str:
    """Shorten long values for step output."""
    if not value:
        return ""
    s = value.strip()
    if len(s) > 400:
        return s[:400] + "..."
    return s


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


def _run_ticket(
    graph,
    ticket: str,
    docs_context: str,
    code_context: str,
) -> None:
    """Run graph with streaming; print current node and step outputs, then final response."""
    initial = {
        "ticket": ticket,
        "classification": "",
        "response": "",
        "docs_context": docs_context,
        "code_context": code_context,
        "full_code_context": code_context,
    }
    final = None
    for mode, chunk in graph.stream(initial, stream_mode=["updates", "values"]):
        if mode == "updates":
            for node_name, update in chunk.items():
                print(f"\n[Node: {node_name}]")
                if not isinstance(update, dict):
                    continue
                if "classification" in update and update["classification"]:
                    print(f"  Classification: {update['classification']}")
                if "response" in update and (update["response"] or "").strip():
                    text = _format_step_value("response", update["response"])
                    print(f"  Response: {text}")
                if "rca_result" in update and (update["rca_result"] or "").strip():
                    text = _format_step_value("rca_result", update["rca_result"])
                    print(f"  RCA: {text}")
                if "suggested_fix" in update and (update["suggested_fix"] or "").strip():
                    diff = (update["suggested_fix"] or "").strip()
                    print(f"  Suggested fix (diff): {len(diff)} chars")
                if "pr_url" in update and (update["pr_url"] or "").strip():
                    print(f"  PR URL: {update['pr_url']}")
        elif mode == "values":
            final = chunk
    if final:
        print(f"\n--- Final ---")
        print(f"Classification: {final.get('classification', '')}")
        response = final.get("response", "")
        if len(response) > _MAX_RESPONSE_LENGTH:
            print(f"Response: {response[:_MAX_RESPONSE_LENGTH]}...")
        else:
            print(f"Response: {response}")


def _run_examples(graph, docs_context: str, code_context: str) -> None:
    """Run built-in example tickets."""
    print("Support ticket classifier (LangGraph POC) — examples\n" + "=" * 50)
    for i, ticket in enumerate(_EXAMPLES, 1):
        print(f"\n--- Example {i} ---")
        print(f"Ticket: {ticket}")
        _run_ticket(graph, ticket, docs_context, code_context)


def _run_interactive(graph, docs_context: str, code_context: str) -> None:
    """Prompt for ticket text and run graph until empty input."""
    print("Support ticket classifier (LangGraph POC)")
    print("Enter your support ticket below. Leave empty and press Enter to quit.\n")
    while True:
        try:
            ticket = input("Ticket: ").strip()
        except EOFError:
            break
        if not ticket:
            break
        print()
        _run_ticket(graph, ticket, docs_context, code_context)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Support ticket classifier (LangGraph). Interactive by default; use 'example' to run built-in examples.",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default=None,
        choices=["example"],
        help="'example' to run built-in example tickets; omit for interactive.",
    )
    args = parser.parse_args()
    use_examples = args.mode == "example"

    _, model = load_anthropic_config()
    if not has_anthropic_key():
        print("ANTHROPIC_API_KEY not set — using demo mode (heuristic classifier, placeholder responses)")
        print("Add ANTHROPIC_API_KEY=sk-ant-... to .env in the project root.\n")
    else:
        print(f"ANTHROPIC_API_KEY loaded — using LLM (model: {model})\n")

    graph = build_graph()
    docs_context = _load_docs_context()
    code_context = _load_code_context()
    if docs_context:
        print("Loaded example_project/docs/USER_DOCS.md as context for question/confusion.\n")
    if code_context:
        print("Loaded example_project source as context for bug RCA/fix.\n")

    if use_examples:
        _run_examples(graph, docs_context, code_context)
    else:
        _run_interactive(graph, docs_context, code_context)


if __name__ == "__main__":
    main()
