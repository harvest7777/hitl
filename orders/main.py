"""
Food Ordering CLI - Main Entry Point

Usage:
    python -m orders.main              # Start new conversation
    python -m orders.main --resume ID  # Resume conversation with thread ID

The thread_id pattern:
    - For CLI: We generate a UUID per session, or accept one via --resume
    - For web app: You'd use your chat_id from your database as the thread_id
    - Same thread_id = same conversation state (cart persists)
"""

import sys
import uuid
from langchain_core.runnables import RunnableConfig

from orders.graph import graph
from orders.checkpointer import setup_checkpointer, cleanup_checkpointer


def main():
    # Handle --resume flag for continuing a previous conversation
    thread_id = None
    if "--resume" in sys.argv:
        idx = sys.argv.index("--resume")
        if idx + 1 < len(sys.argv):
            thread_id = sys.argv[idx + 1]
            print(f"Resuming conversation: {thread_id}")
        else:
            print("Error: --resume requires a thread ID")
            return
    else:
        # New conversation - generate a fresh thread ID
        thread_id = str(uuid.uuid4())
        print(f"Starting new conversation. Thread ID: {thread_id}")
        print("(Save this ID to resume later with --resume)")

    # Initialize PostgreSQL checkpoint tables (idempotent - safe to call multiple times)
    setup_checkpointer()

    try:
        # Config ties this invocation to a specific thread/conversation
        # The checkpointer uses thread_id to store and retrieve state
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        # Check if there's existing state (resuming a conversation)
        existing_state = graph.get_state(config)
        if existing_state.values:
            cart = existing_state.values.get("cart", [])
            if cart:
                print(f"\nResumed with {len(cart)} item(s) in cart.")

        # Welcome message
        print("\n" + "=" * 50)
        print("Welcome to the Food Ordering Bot!")
        print("Type 'menu' to see options, 'help' for commands, 'quit' to exit.")
        print("=" * 50)

        # Main chat loop
        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("Goodbye! Your cart has been saved.")
                print(f"Resume later with: python -m orders.main --resume {thread_id}")
                break

            # Invoke the graph with new user input
            # The graph will:
            # 1. Load existing state from checkpoint (cart, etc.)
            # 2. Merge in new user_input
            # 3. Run through classify_intent -> handler -> END
            # 4. Save updated state to checkpoint
            # 5. Return the final state
            result = graph.invoke(
                {"user_input": user_input},
                config
            )

            # Display the bot's response
            bot_response = result.get("bot_response", "")
            if bot_response:
                print(f"\nBot: {bot_response}")
    finally:
        cleanup_checkpointer()


if __name__ == "__main__":
    main()
