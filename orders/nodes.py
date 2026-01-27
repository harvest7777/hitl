from orders.state import OrderState
from orders.data import format_menu, find_item


def _build_response(message: str, warning: str | None) -> str:
    """Helper to prepend warning to response if present."""
    if warning:
        return f"{warning}\n\n{message}"
    return message


def show_menu(state: OrderState) -> dict:
    """Display the menu to the user."""
    warning = state.get("pending_action_warning")
    menu_text = format_menu()

    return {
        "bot_response": _build_response(menu_text, warning),
        "conversation_stage": "browsing"
    }


def add_to_cart(state: OrderState) -> dict:
    """
    Parse item from user input and add to cart.

    This is a simple keyword match - in production you'd use
    an LLM to extract the item name more intelligently.
    """
    user_input = state.get("user_input", "")
    cart = state.get("cart", []).copy()  # Copy to avoid mutation

    # Try to find a matching menu item
    item = find_item(user_input)

    if item:
        cart.append(item)
        total = sum(i["price"] for i in cart)
        return {
            "cart": cart,
            "bot_response": f"Added {item['name']} (${item['price']:.2f}) to your cart.\n"
                           f"Cart total: ${total:.2f} ({len(cart)} item(s))\n\n"
                           f"Say 'confirm' to checkout, 'cart' to see your order, or keep adding items.",
            "conversation_stage": "ordering"
        }
    else:
        return {
            "bot_response": "I couldn't find that item on the menu. "
                           "Try saying 'menu' to see what's available.",
            "conversation_stage": "ordering"
        }


def show_cart(state: OrderState) -> dict:
    """Display the current cart contents."""
    cart = state.get("cart", [])

    if not cart:
        return {
            "bot_response": "Your cart is empty. Say 'menu' to see what's available!",
            "conversation_stage": "idle"
        }

    lines = ["Your current order:\n"]
    for i, item in enumerate(cart, 1):
        lines.append(f"  {i}. {item['name']} - ${item['price']:.2f}")

    total = sum(item["price"] for item in cart)
    lines.append(f"\nTotal: ${total:.2f}")
    lines.append("\nSay 'confirm' to checkout or 'cancel' to clear your cart.")

    return {
        "bot_response": "\n".join(lines),
        "conversation_stage": "ordering"
    }


def confirm_order(state: OrderState) -> dict:
    """
    Confirm and place the order.

    In production this would:
    - Validate the order
    - Process payment
    - Send to kitchen/fulfillment
    - Return order confirmation number
    """
    cart = state.get("cart", [])

    if not cart:
        return {
            "bot_response": "Your cart is empty! Add some items before confirming.\n"
                           "Say 'menu' to see what's available.",
            "conversation_stage": "idle"
        }

    # "Process" the order
    total = sum(item["price"] for item in cart)
    item_count = len(cart)

    # Clear the cart after order
    return {
        "cart": [],  # Clear cart
        "bot_response": f"Order confirmed! You ordered {item_count} item(s) for ${total:.2f}.\n"
                       f"Thank you for your order!\n\n"
                       f"Say 'menu' to start a new order.",
        "conversation_stage": "idle"
    }


def cancel_order(state: OrderState) -> dict:
    """Cancel the current order and clear the cart."""
    cart = state.get("cart", [])

    if not cart:
        return {
            "bot_response": "Nothing to cancel - your cart is already empty.\n"
                           "Say 'menu' to see what's available.",
            "conversation_stage": "idle"
        }

    item_count = len(cart)
    return {
        "cart": [],  # Clear cart
        "bot_response": f"Order cancelled. Removed {item_count} item(s) from your cart.\n"
                       f"Say 'menu' to start over.",
        "conversation_stage": "idle"
    }


def show_help(state: OrderState) -> dict:
    """Display help information."""
    warning = state.get("pending_action_warning")

    help_text = """Here's how to use this ordering system:

Commands:
  - 'menu'    - See what's available
  - 'cart'    - View your current order
  - 'add X'   - Add item X to your cart (e.g., 'add burger')
  - 'confirm' - Place your order
  - 'cancel'  - Clear your cart and start over
  - 'quit'    - Exit the application

Just type naturally! For example:
  - "I'll have a cheese burger"
  - "Show me the menu"
  - "What's in my cart?"
  - "That's all, checkout please" """

    return {
        "bot_response": _build_response(help_text, warning),
        "conversation_stage": state.get("conversation_stage", "idle")
    }


def handle_unknown(state: OrderState) -> dict:
    """Handle unrecognized input."""
    return {
        "bot_response": "I didn't quite understand that. "
                       "Try 'menu' to see options or 'help' for commands.",
        "conversation_stage": state.get("conversation_stage", "idle")
    }
