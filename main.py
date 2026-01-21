from typing import TypedDict
from langgraph.graph import StateGraph, MessagesState, START, END

# total = false to tell langgraph it is not fully populated at the start
class CustomState(TypedDict, total=False):
    user_input: str
    intent: str
    command_requested_to_execute: str
    confirmed_command: bool 
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
    return {"llm_output": "Please confirm the command"}

def ask_question(state: CustomState):
    return {"llm_output": "Here is the answer to your question"}

def chitchat(state: CustomState):
    return {"llm_output": "Nice chatting with you!"}

"""
ohhhhhhhhhh so i think the pattern is always intent router node which transforms state, a router
function which returns whch node to route to as a edge next, then conditional edge adding
"""
def route_intent(state: CustomState):
    return state.get("intent", "chitchat")

graph = StateGraph(CustomState)
graph.add_node("classify_intent", classify_intent)
graph.add_node("command", parse_command)
graph.add_node("ask_question", ask_question)
graph.add_node("confirm_command", confirm_command)
graph.add_node("chitchat", chitchat)

graph.add_edge(START, "classify_intent")

graph.add_conditional_edges("classify_intent", route_intent, {
    "command": "command",
    "ask_question": "ask_question",
    "chitchat": "chitchat"
})

graph.add_edge("ask_question", END)
graph.add_edge("command", "confirm_command")
graph.add_edge("confirm_command", END)
graph.add_edge("chitchat", END)
graph = graph.compile()

new_state = graph.invoke(CustomState(user_input="/"))
print(new_state)