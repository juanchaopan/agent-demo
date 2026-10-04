from langgraph.graph import END, START, StateGraph
from graph.node import (
    build_activity,
    execute_intents,
    extract_semantics,
    generate_verbose,
)
from model import State


def build_graph(checkpointer=None):
    graph = StateGraph(State)
    graph.add_sequence(
        [extract_semantics, execute_intents, build_activity, generate_verbose]
    )
    graph.add_edge(START, "extract_semantics")
    graph.add_edge("generate_verbose", END)
    return graph.compile(checkpointer=checkpointer)
