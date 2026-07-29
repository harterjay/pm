# Backend

FastAPI app, managed with `uv` (see `pyproject.toml`, `package = false` since this is an app, not a library).

## Structure

- `app/main.py` — FastAPI app; hardcoded credentials (`USERNAME`/`PASSWORD` = `user`/`password`) checked by `POST /api/login`, which sets `request.session["authenticated"]` via Starlette's `SessionMiddleware` (signed cookie, no server-side session store — fine since there's no DB yet). `GET /api/session` reports auth status, `POST /api/logout` clears it. `GET /` and `GET /login` are explicit routes (registered before the static mount, so they win over it) that redirect based on session state instead of always serving a file. `GET /api/health` returns `{"status": "ok"}`. `StaticFiles` mounted at `/` serves everything else in `app/static/` (JS/CSS/images).
- `app/static/` — checked-in placeholder (`index.html`, Part 2 hello-world page) plus `login.html` once Part 4's frontend is built. In the Docker image, the multi-stage build overwrites this directory with the built Next.js static export (`frontend/out/`, see root `Dockerfile`) — `app/main.py` doesn't care which is present, it just serves whatever is on disk.
- `tests/test_main.py` — integration tests using FastAPI's `TestClient`, covering health, session status, login (right/wrong credentials), logout, and the `/` ↔ `/login` redirect behavior in both auth states.

## Auth

`SessionMiddleware` requires `SESSION_SECRET` in the environment (read via `os.environ["SESSION_SECRET"]` — fails fast at startup if missing). It's generated once into the local `.env` (gitignored, loaded by `docker-compose.yml`'s `env_file`); regenerating it invalidates existing sessions, which is harmless for local MVP use.

## Running

Not run directly with `uvicorn` on the host — built and run via Docker (see root `Dockerfile`, `docker-compose.yml`, `scripts/`). Inside the container, `uv sync` installs dependencies and `uv run uvicorn app.main:app` starts the server on port 8000.

## Testing

`pytest` and `httpx` are regular dependencies (not a separate dev group) so `uv sync` always has what's needed to run `uv run pytest`. If `uv` isn't installed on the host, run tests inside the image instead, e.g.:
`docker compose run --rm -v "$(pwd)/backend/tests:/app/backend/tests" --entrypoint "" app uv run pytest -v`
(the tests directory isn't copied into the built image, so it's bind-mounted in for this)

## Known gaps for later parts

- No database (Parts 5-6)
- No Anthropic/AI endpoints (Parts 8-9)