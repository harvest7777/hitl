"""
PostgreSQL Checkpointer Setup

Provides a globally-accessible checkpointer that can be used anywhere
(CLI, FastAPI endpoints, etc.) with connection pooling for efficiency.
"""

import os
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

# Load environment variables from .env file
load_dotenv()

# Get connection string from environment
POSTGRES_CONNECTION_STRING = os.getenv("POSTGRES_CONNECTION_STRING")

if not POSTGRES_CONNECTION_STRING:
    raise ValueError(
        "POSTGRES_CONNECTION_STRING environment variable is not set. "
        "Please add it to your .env file."
    )

# Create a connection pool for efficient connection reuse
# This pool is shared across all graph invocations
_pool = ConnectionPool(
    conninfo=POSTGRES_CONNECTION_STRING,
    min_size=1,
    max_size=10,
    open=True,
)

# Create the checkpointer using the connection pool
checkpointer = PostgresSaver(pool=_pool)


def setup_checkpointer():
    """
    Initialize the checkpoint tables in PostgreSQL.
    Call this once at application startup (e.g., in FastAPI lifespan).
    """
    checkpointer.setup()


def cleanup_checkpointer():
    """
    Close the connection pool.
    Call this at application shutdown.
    """
    _pool.close()
