import sqlite3

from fastapi import HTTPException
from pydantic import BaseModel


class Card(BaseModel):
    id: str
    title: str
    details: str


class Column(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class Board(BaseModel):
    columns: list[Column]
    cards: dict[str, Card]


def _card_public_id(row_id: int) -> str:
    return f"card-{row_id}"


def _parse_card_id(card_id: str) -> int:
    if not card_id.startswith("card-"):
        raise HTTPException(status_code=400, detail="Invalid card id")
    try:
        return int(card_id.removeprefix("card-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid card id")


def _get_board_id(conn: sqlite3.Connection, username: str) -> int:
    row = conn.execute(
        "SELECT b.id FROM boards b JOIN users u ON b.user_id = u.id WHERE u.username = ?",
        (username,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return row["id"]


def _get_column(conn: sqlite3.Connection, board_id: int, column_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM columns WHERE board_id = ? AND slug = ?", (board_id, column_id)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Column not found")
    return row


def _get_card(conn: sqlite3.Connection, board_id: int, card_id: str) -> sqlite3.Row:
    row_id = _parse_card_id(card_id)
    row = conn.execute(
        """
        SELECT cards.* FROM cards
        JOIN columns ON columns.id = cards.column_id
        WHERE columns.board_id = ? AND cards.id = ?
        """,
        (board_id, row_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return row


def _require_title(title: str) -> None:
    if not title.strip():
        raise HTTPException(status_code=422, detail="Title cannot be empty")


def _write_positions(conn: sqlite3.Connection, ordered_ids: list[int]) -> None:
    # Two-phase: stage each row at -id (unique per row) so no intermediate
    # UPDATE can collide with the UNIQUE(column_id, position) constraint,
    # then write the real 0..n-1 positions.
    for card_id in ordered_ids:
        conn.execute("UPDATE cards SET position = ? WHERE id = ?", (-card_id, card_id))
    for index, card_id in enumerate(ordered_ids):
        conn.execute("UPDATE cards SET position = ? WHERE id = ?", (index, card_id))


def get_board(conn: sqlite3.Connection, username: str) -> Board:
    board_id = _get_board_id(conn, username)
    column_rows = conn.execute(
        "SELECT * FROM columns WHERE board_id = ? ORDER BY position", (board_id,)
    ).fetchall()

    columns: list[Column] = []
    cards: dict[str, Card] = {}
    for column_row in column_rows:
        card_rows = conn.execute(
            "SELECT * FROM cards WHERE column_id = ? ORDER BY position",
            (column_row["id"],),
        ).fetchall()
        card_ids = []
        for card_row in card_rows:
            public_id = _card_public_id(card_row["id"])
            card_ids.append(public_id)
            cards[public_id] = Card(
                id=public_id, title=card_row["title"], details=card_row["details"]
            )
        columns.append(
            Column(id=column_row["slug"], title=column_row["title"], cardIds=card_ids)
        )

    return Board(columns=columns, cards=cards)


def rename_column(
    conn: sqlite3.Connection, username: str, column_id: str, title: str
) -> Board:
    _require_title(title)
    board_id = _get_board_id(conn, username)
    column = _get_column(conn, board_id, column_id)
    conn.execute("UPDATE columns SET title = ? WHERE id = ?", (title, column["id"]))
    conn.commit()
    return get_board(conn, username)


def add_card(
    conn: sqlite3.Connection, username: str, column_id: str, title: str, details: str
) -> Board:
    _require_title(title)
    board_id = _get_board_id(conn, username)
    column = _get_column(conn, board_id, column_id)
    next_position = conn.execute(
        "SELECT COALESCE(MAX(position) + 1, 0) FROM cards WHERE column_id = ?",
        (column["id"],),
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
        (column["id"], title, details, next_position),
    )
    conn.commit()
    return get_board(conn, username)


def edit_card(
    conn: sqlite3.Connection, username: str, card_id: str, title: str, details: str
) -> Board:
    _require_title(title)
    board_id = _get_board_id(conn, username)
    card = _get_card(conn, board_id, card_id)
    conn.execute(
        "UPDATE cards SET title = ?, details = ? WHERE id = ?", (title, details, card["id"])
    )
    conn.commit()
    return get_board(conn, username)


def delete_card(conn: sqlite3.Connection, username: str, card_id: str) -> Board:
    board_id = _get_board_id(conn, username)
    card = _get_card(conn, board_id, card_id)
    column_id = card["column_id"]
    conn.execute("DELETE FROM cards WHERE id = ?", (card["id"],))
    remaining_ids = [
        row["id"]
        for row in conn.execute(
            "SELECT id FROM cards WHERE column_id = ? ORDER BY position", (column_id,)
        ).fetchall()
    ]
    _write_positions(conn, remaining_ids)
    conn.commit()
    return get_board(conn, username)


def move_card(
    conn: sqlite3.Connection,
    username: str,
    card_id: str,
    target_column_id: str,
    position: int,
) -> Board:
    board_id = _get_board_id(conn, username)
    card = _get_card(conn, board_id, card_id)
    target_column = _get_column(conn, board_id, target_column_id)
    source_column_id = card["column_id"]
    target_id = target_column["id"]

    # Relocate (and stage at a collision-free position) in one statement.
    conn.execute(
        "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
        (target_id, -card["id"], card["id"]),
    )

    if source_column_id != target_id:
        source_ids = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM cards WHERE column_id = ? ORDER BY position",
                (source_column_id,),
            ).fetchall()
        ]
        _write_positions(conn, source_ids)

    target_ids = [
        row["id"]
        for row in conn.execute(
            "SELECT id FROM cards WHERE column_id = ? AND id != ? ORDER BY position",
            (target_id, card["id"]),
        ).fetchall()
    ]
    clamped_position = max(0, min(position, len(target_ids)))
    target_ids.insert(clamped_position, card["id"])
    _write_positions(conn, target_ids)

    conn.commit()
    return get_board(conn, username)
