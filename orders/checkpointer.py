"""
PostgreSQL Checkpointer Setup

Provides a globally-accessible checkpointer that can be used anywhere
(CLI, FastAPI endpoints, etc.) with connection pooling for efficiency.
"""

import os
from dotenv import load_dotenv
from psycopg import Connection
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

# Create a connection pool for concurrent access
_pool = ConnectionPool(conninfo=POSTGRES_CONNECTION_STRING)

# Create the checkpointer using the pool
checkpointer = PostgresSaver(conn=_pool)


def setup_checkpointer():
    """
    Initialize the checkpoint tables in PostgreSQL.
    Call this once at application startup (e.g., in FastAPI lifespan).

    Uses a separate autocommit connection because CREATE INDEX CONCURRENTLY
    cannot run inside a transaction block.
    """
    with Connection.connect(POSTGRES_CONNECTION_STRING, autocommit=True) as conn:
        temp_saver = PostgresSaver(conn=conn)
        temp_saver.setup()


def cleanup_checkpointer():
    """
    Close the connection pool.
    Call this at application shutdown.
    """
    _pool.close()
