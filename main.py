from typing import TypedDict
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

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


checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}


state_1 = graph.invoke(CustomState(user_input="/"), config)
print(graph.get_state(config).values)
print(state_1)

