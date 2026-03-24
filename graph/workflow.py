"""
graph/workflow.py
Compiled LangGraph workflow for Memoria.
"""

from langgraph.graph import StateGraph, END
from graph.state import MemoriaState
from graph.nodes import resolve_node, guard_node, retrieve_node, generate_node


def should_retrieve(state: MemoriaState) -> str:
    """
    Routing function after guard_node.
    If any profiles are allowed → retrieve context.
    If all denied → skip to generate (which handles denial).
    """
    if state["allowed_profiles"]:
        return "retrieve"
    return "generate"


def build_workflow():
    graph = StateGraph(MemoriaState)

    # Add nodes
    graph.add_node("resolve",  resolve_node)
    graph.add_node("guard",    guard_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)

    # Edges
    graph.set_entry_point("resolve")
    graph.add_edge("resolve", "guard")

    # Conditional edge after guard
    graph.add_conditional_edges(
        "guard",
        should_retrieve,
        {
            "retrieve": "retrieve",
            "generate": "generate",
        }
    )

    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


# Singleton compiled graph
memoria_graph = build_workflow()
