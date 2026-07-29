import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app import ai as ai_module
from app import board as board_module
from app.db import get_connection, init_db

USERNAME = "user"
PASSWORD = "password"

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    try:
        init_db(conn)
    finally:
        conn.close()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.environ["SESSION_SECRET"])


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def require_user(request: Request) -> str:
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username


class LoginRequest(BaseModel):
    username: str
    password: str


class RenameColumnRequest(BaseModel):
    title: str


class AddCardRequest(BaseModel):
    title: str
    details: str = ""


class EditCardRequest(BaseModel):
    title: str
    details: str = ""


class MoveCardRequest(BaseModel):
    columnId: str
    position: int


class AskRequest(BaseModel):
    prompt: str


class AskResponse(BaseModel):
    reply: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/session")
def session_status(request: Request) -> dict[str, bool]:
    return {"authenticated": bool(request.session.get("username"))}


@app.post("/api/login")
def login(credentials: LoginRequest, request: Request) -> dict[str, bool]:
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    request.session["username"] = credentials.username
    return {"authenticated": True}


@app.post("/api/logout")
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"authenticated": False}


@app.get("/api/board", response_model=board_module.Board)
def read_board(
    username: str = Depends(require_user), conn: sqlite3.Connection = Depends(get_db)
) -> board_module.Board:
    return board_module.get_board(conn, username)


@app.patch("/api/board/columns/{column_id}", response_model=board_module.Board)
def rename_column_route(
    column_id: str,
    payload: RenameColumnRequest,
    username: str = Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> board_module.Board:
    return board_module.rename_column(conn, username, column_id, payload.title)


@app.post("/api/board/columns/{column_id}/cards", response_model=board_module.Board)
def add_card_route(
    column_id: str,
    payload: AddCardRequest,
    username: str = Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> board_module.Board:
    return board_module.add_card(conn, username, column_id, payload.title, payload.details)


@app.patch("/api/board/cards/{card_id}", response_model=board_module.Board)
def edit_card_route(
    card_id: str,
    payload: EditCardRequest,
    username: str = Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> board_module.Board:
    return board_module.edit_card(conn, username, card_id, payload.title, payload.details)


@app.delete("/api/board/cards/{card_id}", response_model=board_module.Board)
def delete_card_route(
    card_id: str,
    username: str = Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> board_module.Board:
    return board_module.delete_card(conn, username, card_id)


@app.post("/api/board/cards/{card_id}/move", response_model=board_module.Board)
def move_card_route(
    card_id: str,
    payload: MoveCardRequest,
    username: str = Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> board_module.Board:
    return board_module.move_card(conn, username, card_id, payload.columnId, payload.position)


@app.post("/api/ai/ask", response_model=AskResponse)
def ask_ai(payload: AskRequest, username: str = Depends(require_user)) -> AskResponse:
    return AskResponse(reply=ai_module.ask(payload.prompt))


@app.get("/")
def index(request: Request):
    if not request.session.get("username"):
        return RedirectResponse("/login")
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/login")
def login_page(request: Request):
    if request.session.get("username"):
        return RedirectResponse("/")
    return FileResponse(STATIC_DIR / "login.html")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
