import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

USERNAME = "user"
PASSWORD = "password"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ["SESSION_SECRET"])

STATIC_DIR = Path(__file__).parent / "static"


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/session")
def session_status(request: Request) -> dict[str, bool]:
    return {"authenticated": bool(request.session.get("authenticated"))}


@app.post("/api/login")
def login(credentials: LoginRequest, request: Request) -> dict[str, bool]:
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    request.session["authenticated"] = True
    return {"authenticated": True}


@app.post("/api/logout")
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"authenticated": False}


@app.get("/")
def index(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse("/login")
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/login")
def login_page(request: Request):
    if request.session.get("authenticated"):
        return RedirectResponse("/")
    return FileResponse(STATIC_DIR / "login.html")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
