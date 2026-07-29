import hashlib
import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pm.db"

SEED_USERNAME = "user"
SEED_COLUMNS = [
    ("col-backlog", "Backlog"),
    ("col-discovery", "Discovery"),
    ("col-progress", "In Progress"),
    ("col-review", "Review"),
    ("col-done", "Done"),
]
SEED_CARDS = {
    "col-backlog": [
        ("Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
        ("Gather customer signals", "Review support tags, sales notes, and churn feedback."),
    ],
    "col-discovery": [
        ("Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
    ],
    "col-progress": [
        ("Refine status language", "Standardize column labels and tone across the board."),
        ("Design card layout", "Add hierarchy and spacing for scanning dense lists."),
    ],
    "col-review": [
        ("QA micro-interactions", "Verify hover, focus, and loading states."),
    ],
    "col-done": [
        ("Ship marketing page", "Final copy approved and asset pack delivered."),
        ("Close onboarding sprint", "Document release notes and share internally."),
    ],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE(board_id, slug),
    UNIQUE(board_id, position)
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    position INTEGER NOT NULL,
    UNIQUE(column_id, position)
);
"""


def get_db_path() -> Path:
    return Path(os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH))


def get_connection() -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
    _seed_if_empty(conn)


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        return

    password_hash = hashlib.sha256(b"password").hexdigest()
    user_id = conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (SEED_USERNAME, password_hash),
    ).lastrowid
    board_id = conn.execute(
        "INSERT INTO boards (user_id) VALUES (?)", (user_id,)
    ).lastrowid

    for position, (slug, title) in enumerate(SEED_COLUMNS):
        column_id = conn.execute(
            "INSERT INTO columns (board_id, slug, title, position) VALUES (?, ?, ?, ?)",
            (board_id, slug, title, position),
        ).lastrowid
        for card_position, (card_title, details) in enumerate(SEED_CARDS[slug]):
            conn.execute(
                "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
                (column_id, card_title, details, card_position),
            )

    conn.commit()
