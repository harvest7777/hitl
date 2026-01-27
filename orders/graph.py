from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

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


def create_graph(checkpointer: BaseCheckpointSaver):
    """
    Build and compile the order workflow graph.

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

    The checkpointer persists state between invocations, allowing
    the conversation to resume where it left off.
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

    # =========================================================================
    # COMPILE
    # Compilation validates the graph and attaches the checkpointer
    # =========================================================================
    return workflow.compile(checkpointer=checkpointer)
