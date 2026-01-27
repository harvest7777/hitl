# Mock menu data for the ordering system
# This would be replaced with a database call in production

MENU = {
    "Burgers": [
        {"name": "Classic Burger", "price": 8.99},
        {"name": "Cheese Burger", "price": 9.99},
        {"name": "Bacon Burger", "price": 11.99},
    ],
    "Pizza": [
        {"name": "Margherita", "price": 12.99},
        {"name": "Pepperoni", "price": 14.99},
        {"name": "Veggie Supreme", "price": 13.99},
    ],
    "Drinks": [
        {"name": "Soda", "price": 2.99},
        {"name": "Juice", "price": 3.99},
        {"name": "Water", "price": 1.99},
    ],
}


def get_all_items() -> list[dict]:
    """Flatten menu into a list of all items with their category."""
    items = []
    for category, category_items in MENU.items():
        for item in category_items:
            items.append({**item, "category": category})
    return items


def find_item(query: str) -> dict | None:
    """
    Find a menu item by name (case-insensitive partial match).

    Checks if any item name appears in the user's query.
    Example: "add cheese burger please" matches "Cheese Burger"
    """
    query_lower = query.lower()
    for item in get_all_items():
        # Check if the item name appears in the user's input
        if item["name"].lower() in query_lower:
            return item
    return None


def format_menu() -> str:
    """Format the menu for display."""
    lines = ["Here's our menu:\n"]
    for category, items in MENU.items():
        lines.append(f"\n{category}:")
        for item in items:
            lines.append(f"  - {item['name']}: ${item['price']:.2f}")
    return "\n".join(lines)
