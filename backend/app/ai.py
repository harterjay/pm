import sqlite3
from typing import Literal, Union

import anthropic
from fastapi import HTTPException
from pydantic import BaseModel

from app import board as board_module
from app.board import Board

MODEL = "claude-sonnet-5"


def ask(prompt: str) -> str:
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
    except (anthropic.AnthropicError, TypeError) as exc:
        # A missing API key/credentials surfaces as a raw TypeError from the
        # SDK's header validation (not an AnthropicError subclass), so it's
        # caught explicitly here alongside the normal SDK error hierarchy.
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc

    return "".join(block.text for block in response.content if block.type == "text")


class RenameColumnAction(BaseModel):
    type: Literal["rename_column"]
    column_id: str
    title: str


class AddCardAction(BaseModel):
    type: Literal["add_card"]
    column_id: str
    title: str
    details: str = ""


class EditCardAction(BaseModel):
    type: Literal["edit_card"]
    card_id: str
    title: str
    details: str = ""


class DeleteCardAction(BaseModel):
    type: Literal["delete_card"]
    card_id: str


class MoveCardAction(BaseModel):
    type: Literal["move_card"]
    card_id: str
    column_id: str
    position: int


BoardAction = Union[
    RenameColumnAction, AddCardAction, EditCardAction, DeleteCardAction, MoveCardAction
]


class ChatReply(BaseModel):
    reply: str
    action: BoardAction | None = None


FALLBACK_REPLY = "Sorry, I couldn't come up with a response to that. Please try again."

CHAT_SYSTEM_PROMPT = """You are the assistant for a Kanban board app called Kanban Studio.

Reply conversationally to the user's message. If, and only if, the user explicitly \
asked for a change to the board (creating, editing, deleting, or moving a card, or \
renaming a column), also include a single action describing that change. For \
questions or general conversation, leave the action unset.

Column and card ids in an action must be ids that already exist on the current board \
below - never invent one. position is a 0-based index within the target column; if \
the user didn't ask for a specific position, use a large number (e.g. 999) to place \
the card at the end.

Current board (JSON): {board_json}"""


def chat(board: Board, message: str, history: list[dict[str, str]]) -> ChatReply:
    system = CHAT_SYSTEM_PROMPT.format(board_json=board.model_dump_json())
    messages = [dict(entry) for entry in history]
    messages.append({"role": "user", "content": message})

    try:
        client = anthropic.Anthropic()
        response = client.messages.parse(
            model=MODEL,
            max_tokens=1024,
            system=system,
            messages=messages,
            output_format=ChatReply,
        )
    except (anthropic.AnthropicError, TypeError):
        return ChatReply(reply=FALLBACK_REPLY)

    return response.parsed_output or ChatReply(reply=FALLBACK_REPLY)


def apply_action(conn: sqlite3.Connection, username: str, action: BoardAction) -> Board:
    if isinstance(action, RenameColumnAction):
        return board_module.rename_column(conn, username, action.column_id, action.title)
    if isinstance(action, AddCardAction):
        return board_module.add_card(
            conn, username, action.column_id, action.title, action.details
        )
    if isinstance(action, EditCardAction):
        return board_module.edit_card(conn, username, action.card_id, action.title, action.details)
    if isinstance(action, DeleteCardAction):
        return board_module.delete_card(conn, username, action.card_id)
    if isinstance(action, MoveCardAction):
        return board_module.move_card(
            conn, username, action.card_id, action.column_id, action.position
        )
    raise ValueError(f"Unknown action type: {action}")
