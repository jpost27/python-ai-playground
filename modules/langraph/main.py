"""
Support ticket classifier — LangGraph POC.

Routes tickets: question → answer, confusion → suggest help, bug → root cause (placeholder).
Run: uv run python -m modules.langraph.main
"""

from modules.langraph.config import has_anthropic_key, load_anthropic_config
from modules.langraph.graph import build_graph


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

    print("Support ticket classifier (LangGraph POC)\n" + "=" * 50)
    for i, ticket in enumerate(examples, 1):
        print(f"\n--- Example {i} ---")
        print(f"Ticket: {ticket}")
        result = graph.invoke({"ticket": ticket, "classification": "", "response": ""})
        print(f"Classification: {result['classification']}")
        response = result.get("response", "")
        print(f"Response: {response[:200]}..." if len(response) > 200 else f"Response: {response}")


if __name__ == "__main__":
    main()
