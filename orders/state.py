from typing import TypedDict


class OrderState(TypedDict, total=False):
    """
    State for the food ordering conversation.

    Using total=False means fields are optional - LangGraph will merge
    partial state updates into the full state automatically.
    """

    # Current user message - updated each turn
    user_input: str

    # Classified intent from routing.py
    # One of: "view_menu", "add_item", "view_cart", "confirm", "cancel", "help", "unknown"
    intent: str

    # Shopping cart - list of items with name and price
    # Example: [{"name": "Cheese Burger", "price": 9.99, "category": "Burgers"}]
    cart: list[dict]

    # Response to display to user
    bot_response: str

    # Tracks where user is in the flow: "idle", "browsing", "ordering", "confirming"
    # This helps with context-aware intent detection (future LLM use)
    conversation_stage: str

    # Warning shown when user has pending items and changes topic
    # Example: "Note: You have 2 item(s) in your cart."
    pending_action_warning: str | None
