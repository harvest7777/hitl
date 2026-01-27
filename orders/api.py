"""
FastAPI Example - Using the graph in API endpoints

Usage:
    uvicorn orders.api:app --reload

The graph with PostgreSQL checkpointer can be imported and used directly
in any FastAPI endpoint. The connection pool handles concurrent requests.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig

from orders.graph import graph
from orders.checkpointer import setup_checkpointer, cleanup_checkpointer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize checkpointer on startup, cleanup on shutdown."""
    setup_checkpointer()
    yield
    cleanup_checkpointer()


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    thread_id: str
    message: str


class ChatResponse(BaseModel):
    thread_id: str
    response: str
    cart_count: int


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Send a message to the food ordering bot.

    The thread_id maintains conversation state - use the same thread_id
    to continue a conversation, or a new one to start fresh.
    """
    config: RunnableConfig = {"configurable": {"thread_id": request.thread_id}}

    result = graph.invoke(
        {"user_input": request.message},
        config
    )

    cart = result.get("cart", [])

    return ChatResponse(
        thread_id=request.thread_id,
        response=result.get("bot_response", ""),
        cart_count=len(cart),
    )


@app.get("/cart/{thread_id}")
def get_cart(thread_id: str):
    """Get the current cart for a conversation."""
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    state = graph.get_state(config)
    cart = state.values.get("cart", []) if state.values else []

    return {"thread_id": thread_id, "cart": cart}
