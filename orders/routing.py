from orders.state import OrderState


def detect_intent(user_input: str) -> str:
    """
    Hardcoded intent detection based on keywords.

    In a real app, this would be replaced with an LLM call that can
    understand context and nuance. For now, simple keyword matching.

    Returns one of:
        - "view_menu": User wants to see the menu
        - "add_item": User wants to add something to cart
        - "view_cart": User wants to see their current order
        - "confirm": User wants to confirm/checkout
        - "cancel": User wants to cancel the order
        - "help": User needs help
        - "unknown": Couldn't determine intent
    """
    text = user_input.lower()

    # Order matters - check more specific patterns first

    if any(word in text for word in ["menu", "options", "what do you have", "what's available"]):
        return "view_menu"

    if any(word in text for word in ["cart", "my order", "what did i", "show order"]):
        return "view_cart"

    if any(word in text for word in ["add", "order", "want", "get", "i'll have", "give me"]):
        return "add_item"

    if any(word in text for word in ["confirm", "checkout", "done", "that's all", "place order", "submit"]):
        return "confirm"

    if any(word in text for word in ["cancel", "nevermind", "forget it", "clear", "start over"]):
        return "cancel"

    if any(word in text for word in ["help", "how do i", "?"]):
        return "help"

    return "unknown"


def classify_intent(state: OrderState) -> dict:
    """
    Node function: Classifies user intent and checks for pending actions.

    This is the entry point for every user message. It:
    1. Detects the intent from user_input
    2. Checks if user has items in cart and is "leaving" the order flow
    3. Adds a warning if so (the "warn and preserve" behavior)

    Returns partial state update with intent and optional warning.
    """
    user_input = state.get("user_input", "")
    intent = detect_intent(user_input)

    # Check for pending items when user navigates away
    cart = state.get("cart", [])
    has_pending_items = len(cart) > 0

    # These intents are "leaving" the order flow - user might forget their cart
    leaving_intents = ["view_menu", "help"]

    if has_pending_items and intent in leaving_intents:
        return {
            "intent": intent,
            "pending_action_warning": f"Note: You have {len(cart)} item(s) in your cart."
        }

    # Clear any previous warning
    return {
        "intent": intent,
        "pending_action_warning": None
    }


def route_intent(state: OrderState) -> str:
    """
    Router function: Returns the next node name based on intent.

    This is used with add_conditional_edges to route to the right handler.
    The string returned must match a node name in the graph.
    """
    intent = state.get("intent", "unknown")

    # Map intents to node names
    # These must match the node names added in graph.py
    routes = {
        "view_menu": "show_menu",
        "add_item": "add_to_cart",
        "view_cart": "show_cart",
        "confirm": "confirm_order",
        "cancel": "cancel_order",
        "help": "show_help",
        "unknown": "handle_unknown",
    }

    return routes.get(intent, "handle_unknown")
