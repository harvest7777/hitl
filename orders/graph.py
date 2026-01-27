from langgraph.graph import StateGraph, START, END

from orders.state import OrderState
from orders.routing import classify_intent, route_intent
from orders.nodes import (
    show_menu,
    add_to_cart,
    show_cart,
    confirm_order,
    cancel_order,
    show_help,
    handle_unknown,
)
from orders.checkpointer import checkpointer


def _build_workflow() -> StateGraph:
    """
    Build the order workflow graph (uncompiled).

    Graph structure:
        START
          |
          v
        classify_intent  <-- Every message enters here first
          |
          v (conditional routing based on intent)
        [show_menu | add_to_cart | show_cart | confirm_order | cancel_order | show_help | handle_unknown]
          |
          v
         END  <-- Graph pauses here, waiting for next user input
    """
    workflow = StateGraph(OrderState)

    # =========================================================================
    # ADD NODES
    # Each node is a function that takes state and returns a partial state update
    # =========================================================================

    # Entry point: classify what the user wants
    workflow.add_node("classify_intent", classify_intent)

    # Handler nodes - one for each intent type
    workflow.add_node("show_menu", show_menu)
    workflow.add_node("add_to_cart", add_to_cart)
    workflow.add_node("show_cart", show_cart)
    workflow.add_node("confirm_order", confirm_order)
    workflow.add_node("cancel_order", cancel_order)
    workflow.add_node("show_help", show_help)
    workflow.add_node("handle_unknown", handle_unknown)

    # =========================================================================
    # ADD EDGES
    # Edges define how execution flows between nodes
    # =========================================================================

    # START -> classify_intent: Every conversation turn starts here
    workflow.add_edge(START, "classify_intent")

    # classify_intent -> [handler]: Route to appropriate handler based on intent
    # The route_intent function returns a string matching one of these node names
    workflow.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "show_menu": "show_menu",
            "add_to_cart": "add_to_cart",
            "show_cart": "show_cart",
            "confirm_order": "confirm_order",
            "cancel_order": "cancel_order",
            "show_help": "show_help",
            "handle_unknown": "handle_unknown",
        }
    )

    # All handlers -> END: After handling, pause and wait for next input
    # This is what makes it a "chat" - graph runs, responds, then stops
    workflow.add_edge("show_menu", END)
    workflow.add_edge("add_to_cart", END)
    workflow.add_edge("show_cart", END)
    workflow.add_edge("confirm_order", END)
    workflow.add_edge("cancel_order", END)
    workflow.add_edge("show_help", END)
    workflow.add_edge("handle_unknown", END)

    return workflow


# Build and compile the graph with PostgreSQL checkpointer
# This graph instance can be imported and used anywhere (FastAPI, CLI, etc.)
graph = _build_workflow().compile(checkpointer=checkpointer)
