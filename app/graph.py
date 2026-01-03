# graph.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any

from nodes.validator import validate_problem
from nodes.selector import find_experts


class GraphState(TypedDict, total=False):
    problem: str
    validation: Dict[str, Any]
    expert_data: Dict[str, Any]


def build_graph():
    graph = StateGraph(GraphState)

    # Nodes
    graph.add_node("validator", validate_problem)
    graph.add_node("expert_finder", find_experts)

    # Flow
    graph.set_entry_point("validator")
    graph.add_edge("validator", "expert_finder")
    graph.add_edge("expert_finder", END)

    return graph.compile()


graph_app = build_graph()


async def run_graph(problem: str) -> Dict[str, Any]:
    """
    Runs validation + expert selection only.
    NO streaming here.
    """

    result = await graph_app.ainvoke({"problem": problem})

    # Explicit contract: what the graph guarantees to return
    return {
        "problem": problem,
        "expert_data": result["expert_data"]
    }
