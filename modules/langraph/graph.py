"""LangGraph definition: nodes, routing, compiled graph."""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from modules.langraph.state import CONFUSION, QUESTION, TicketState
from modules.langraph import nodes

# Node names (must match add_node keys and route return values)
NODE_ANSWER = "answer_question"
NODE_SUGGEST = "suggest_help"
NODE_ROOT_CAUSE = "root_cause_analysis"


def route_by_classification(
    state: TicketState,
) -> Literal["answer_question", "suggest_help", "root_cause_analysis"]:
    """Route to the handler for this classification."""
    c = state.get("classification", QUESTION)
    if c == QUESTION:
        return NODE_ANSWER
    if c == CONFUSION:
        return NODE_SUGGEST
    return NODE_ROOT_CAUSE


def build_graph() -> StateGraph:
    """Build and compile the support-ticket graph."""
    builder = StateGraph(TicketState)

    builder.add_node("classify", nodes.classify_ticket)
    builder.add_node(NODE_ANSWER, nodes.answer_question)
    builder.add_node(NODE_SUGGEST, nodes.suggest_help)
    builder.add_node(NODE_ROOT_CAUSE, nodes.root_cause_analysis)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route_by_classification)
    builder.add_edge(NODE_ANSWER, END)
    builder.add_edge(NODE_SUGGEST, END)
    builder.add_edge(NODE_ROOT_CAUSE, END)

    return builder.compile()
