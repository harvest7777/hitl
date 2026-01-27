import sys
import os
from typing import TypedDict
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.runnables import RunnableConfig

# ============================================================================
# PROOF OF CONCEPT: Resuming a LangGraph from SQLite checkpoint
#
# Usage:
#   python main.py          # Run 1: starts graph, pauses at confirmation
#   python main.py          # Run 2: resumes from checkpoint, confirms command
#   python main.py --reset  # Delete checkpoint and start fresh
# ============================================================================

# Helper to reset checkpoint for testing
if "--reset" in sys.argv:
    if os.path.exists("checkpoints.db"):
        os.remove("checkpoints.db")
        print("Checkpoint deleted. Starting fresh on next run.")
    sys.exit(0)

# total = false to tell langgraph it is not fully populated at the start
class CustomState(TypedDict, total=False):
    user_input: str
    intent: str
    command_requested_to_execute: str
    confirmed_command: bool | None
    llm_output: str

def classify_intent(state: CustomState):
    if "?" in state["user_input"]:
        return {"intent": "ask_question"}
    elif "/" in state["user_input"]:
        return {"intent": "command"}
    else:
        return {"intent": "chitchat"}

def parse_command(state: CustomState):
    return {"command": "freaky_mode"}

def confirm_command(state: CustomState):
    if "yes" in state.get("user_input"):
        return {"confirmed_command": True}

    if "no" in state.get("user_input"):
        return {"confirmed_command": False}

    return {"llm_output": "Please confirm the command"}

def execute_command(state: CustomState):
    return {"llm_output": "freaky mode ON 😈"}

def cancel_command(state: CustomState):
    return {"confirmed_command": False, "llm_output": "cancelled"}

def ask_question(state: CustomState):
    return {"llm_output": "Here is the answer to your question"}

def chitchat(state: CustomState):
    return {"llm_output": "Nice chatting with you!"}

"""
ohhhhhhhhhh so i think the pattern is always intent router node which transforms state, a router
function which returns whch node to route to as a edge next, then conditional edge adding
"""
def route_intent(state: CustomState):
    intent = state.get("intent", "chitchat")
    return intent

def route_confirmation(state: CustomState):
    if state.get("confirmed_command") == True:
        return "execute_command"
    if state.get("confirmed_command") == False:
        return "cancel_command"

    # we are awaiting confirmation
    return END

workflow = StateGraph(CustomState)

workflow.add_node("classify_intent", classify_intent)
workflow.add_node("command", parse_command)
workflow.add_node("execute_command", execute_command)
workflow.add_node("cancel_command", cancel_command)
workflow.add_node("ask_question", ask_question)
workflow.add_node("confirm_command", confirm_command)
workflow.add_node("chitchat", chitchat)

workflow.add_edge(START, "classify_intent")

workflow.add_conditional_edges("classify_intent", route_intent, {
    "command": "command",
    "ask_question": "ask_question",
    "chitchat": "chitchat"
})

workflow.add_edge("command", "confirm_command")

"""
You want conditional edges from the node that just produced the information needed to decide.
thats whyw e do conditional edges for all command stuff from the command ndoe
"""
workflow.add_conditional_edges("confirm_command", route_confirmation, {
    "cancel_command": "cancel_command",
    "execute_command": "execute_command",
    END: END
})

workflow.add_edge("ask_question", END)
workflow.add_edge("command", "confirm_command")
workflow.add_edge("chitchat", END)
workflow.add_edge("cancel_command", END)
workflow.add_edge("execute_command", END)


with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = workflow.compile(checkpointer=checkpointer)

    # thread_id is the key for persisting/resuming state
    # same thread_id = same conversation, can resume where it left off
    config: RunnableConfig = {"configurable": {"thread_id": "1"}}

    # Check if there's existing state for this thread
    # This is how you detect if you're resuming vs starting fresh
    existing_state = graph.get_state(config)

    if existing_state.values:
        # RESUMING: There's existing state from a previous run
        # The graph paused at confirm_command waiting for user input
        print("=== RESUMING FROM CHECKPOINT ===")
        print(f"Previous state: {existing_state.values}")
        print(f"Graph paused at: {existing_state.next}")  # shows which node(s) are next

        # To resume, just invoke again with new input
        # The graph picks up from where it left off (confirm_command node)
        # and uses the new user_input to make the confirmation decision
        result = graph.invoke(
            {"user_input": "yes"},  # user confirms the command
            config
        )
        print(f"Final state after resume: {result}")

    else:
        # FRESH START: No existing state, start from the beginning
        print("=== STARTING FRESH ===")

        # This will run: START -> classify_intent -> command -> confirm_command -> END
        # The graph pauses at END after confirm_command because we haven't confirmed yet
        result = graph.invoke(
            {"user_input": "/do_something"},
            config
        )
        print(f"State after first run: {result}")
        print(f"Graph paused at: {graph.get_state(config).next}")
        print("\n>>> Run the script again to see it resume from checkpoint! <<<")

