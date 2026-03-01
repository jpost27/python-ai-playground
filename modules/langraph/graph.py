"""LangGraph definition: nodes, routing, compiled graph."""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from modules.langraph.state import CONFUSION, QUESTION, TicketState
from modules.langraph import nodes

# Node names (must match add_node keys and route return values)
NODE_RETRIEVE_DOCS = "retrieve_docs"
NODE_ANSWER = "answer_question"
NODE_SUGGEST = "suggest_help"
NODE_ROOT_CAUSE = "root_cause_analysis"
NODE_PROPOSE_FIX = "propose_fix"
NODE_CREATE_PR = "create_pr"


def route_by_classification(
    state: TicketState,
) -> Literal["retrieve_docs", "root_cause_analysis"]:
    """Route: question/confusion → retrieve_docs (then to answer/suggest); bug → root_cause."""
    c = state.get("classification", QUESTION)
    if c in (QUESTION, CONFUSION):
        return NODE_RETRIEVE_DOCS
    return NODE_ROOT_CAUSE


def route_after_retrieve(
    state: TicketState,
) -> Literal["answer_question", "suggest_help"]:
    """After retrieve_docs, route to answer (question) or suggest (confusion)."""
    c = state.get("classification", QUESTION)
    return NODE_ANSWER if c == QUESTION else NODE_SUGGEST


def build_graph() -> StateGraph:
    """Build and compile the support-ticket graph."""
    builder = StateGraph(TicketState)

    builder.add_node("classify", nodes.classify_ticket)
    builder.add_node(NODE_RETRIEVE_DOCS, nodes.retrieve_docs)
    builder.add_node(NODE_ANSWER, nodes.answer_question)
    builder.add_node(NODE_SUGGEST, nodes.suggest_help)
    builder.add_node(NODE_ROOT_CAUSE, nodes.root_cause_analysis)
    builder.add_node(NODE_PROPOSE_FIX, nodes.propose_fix)
    builder.add_node(NODE_CREATE_PR, nodes.create_pr)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route_by_classification)
    builder.add_conditional_edges(NODE_RETRIEVE_DOCS, route_after_retrieve)
    builder.add_edge(NODE_ANSWER, END)
    builder.add_edge(NODE_SUGGEST, END)
    builder.add_edge(NODE_ROOT_CAUSE, NODE_PROPOSE_FIX)
    builder.add_edge(NODE_PROPOSE_FIX, NODE_CREATE_PR)
    builder.add_edge(NODE_CREATE_PR, END)

    return builder.compile()
