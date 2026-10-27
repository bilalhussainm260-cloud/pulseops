
import os
import sqlite3
from pathlib import Path

# Database location:
# Windows: application/orders.db
# Docker: /data/orders.db

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "orders.db"

DB_PATH = Path(
    os.getenv("PULSEOPS_DB_PATH", str(DEFAULT_DB_PATH))
)


def get_connection():
    """Create a connection to the SQLite database."""

    # Create database directory if it does not exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    """Create the orders table if it does not exist."""

    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            )
            """
        )

        connection.commit()

    finally:
        connection.close()
