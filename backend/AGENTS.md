# Backend

FastAPI app, managed with `uv` (see `pyproject.toml`, `package = false` since this is an app, not a library).

## Structure

- `app/main.py` — FastAPI app and route wiring. Hardcoded credentials (`USERNAME`/`PASSWORD` = `user`/`password`) checked by `POST /api/login`, which sets `request.session["username"]` via Starlette's `SessionMiddleware` (signed cookie). `GET /api/session` reports auth status, `POST /api/logout` clears it. `GET /` and `GET /login` are explicit routes (registered before the static mount, so they win over it) that redirect based on session state instead of always serving a file. `GET /api/health` returns `{"status": "ok"}`. `StaticFiles` mounted at `/` serves everything else in `app/static/` (JS/CSS/images). The `/api/board*` routes (below) all depend on `require_user`, which 401s if `request.session["username"]` is unset.
- `app/db.py` — SQLite connection/schema/seed. `get_connection()` opens a file at `DATABASE_PATH` env var (default `backend/data/pm.db`, sibling of `app/`), creating parent dirs as needed. `init_db()` runs idempotent `CREATE TABLE IF NOT EXISTS` for `users`/`boards`/`columns`/`cards` (schema matches `docs/schema.json`) and seeds the demo user/board/columns/cards only when `users` is empty — runs once at app startup via the `lifespan` context manager in `main.py`.
- `app/board.py` — board CRUD, operating on a raw `sqlite3.Connection` (no ORM). `get_board`/`rename_column`/`add_card`/`edit_card`/`delete_card`/`move_card`, plus the `Board`/`Column`/`Card` Pydantic response models. Every mutation returns the full updated `Board` (simplest contract for Part 7's frontend — no partial-update reconciliation needed). Column ids are the DB `slug` (e.g. `col-backlog`) used verbatim; card ids are `f"card-{db_id}"`. `move_card` reorders/relocates via a two-phase position rewrite (stage each row at `-id`, a value unique per row, before writing final `0..n-1` positions) to avoid transient collisions with the `UNIQUE(column_id, position)` constraint — see the docstring-less comment in `_write_positions` if touching this.
- `app/static/` — checked-in placeholder (`index.html`, Part 2 hello-world page) plus `login.html` once Part 4's frontend is built. In the Docker image, the multi-stage build overwrites this directory with the built Next.js static export (`frontend/out/`, see root `Dockerfile`) — `app/main.py` doesn't care which is present, it just serves whatever is on disk.
- `app/ai.py` — `ask(prompt) -> str`, a thin wrapper around the `anthropic` SDK. Constructs `anthropic.Anthropic()` (reads `ANTHROPIC_API_KEY` from the environment) fresh per call rather than once at import/startup, so a missing/invalid key can't crash the app at boot and env changes (e.g. in tests) take effect immediately. `POST /api/ai/ask` (behind `require_user`, like the board routes) wraps it — model is `claude-sonnet-5` per CLAUDE.md.
- `tests/conftest.py` — shared `client` / `logged_in_client` fixtures (isolated DB, `TestClient` as a context manager so `lifespan` runs) used by every test file.
- `tests/test_main.py` — integration tests using FastAPI's `TestClient`, covering health, session status, login (right/wrong credentials), logout, the `/` ↔ `/login` redirect behavior, DB file creation-when-missing/reuse-when-present, and full board CRUD + move including edge cases (invalid card id format, empty titles, nonexistent column/card).
- `tests/test_ai.py` — a *live* round-trip test against the real Anthropic API ("what is 2+2?" → asserts `"4"` in the reply, using the key in `.env`) plus auth-required and missing/invalid-API-key cases. The invalid-key case is a genuine gotcha: with zero resolvable credentials, the SDK raises a bare `TypeError` at request time (not an `anthropic.AnthropicError` subclass) — `ai.ask()` catches `(anthropic.AnthropicError, TypeError)` specifically because of this; the invalid-but-present-key case does raise `AnthropicError` normally.

## Auth

`SessionMiddleware` requires `SESSION_SECRET` in the environment (read via `os.environ["SESSION_SECRET"]` — fails fast at startup if missing). It's generated once into the local `.env` (gitignored, loaded by `docker-compose.yml`'s `env_file`); regenerating it invalidates existing sessions, which is harmless for local MVP use.

## Database

SQLite file at `backend/data/pm.db` (gitignored — runtime state, not source). `docker-compose.yml` bind-mounts `./backend/data` onto the container's `/app/backend/data` so it survives `docker compose down`/`up`. No migration framework — see `docs/DATABASE.md` for the full rationale and the id-mapping approach (why column/card ids come out matching the frontend's original hardcoded seed ids with zero translation).

## Running

Not run directly with `uvicorn` on the host — built and run via Docker (see root `Dockerfile`, `docker-compose.yml`, `scripts/`). Inside the container, `uv sync` installs dependencies and `uv run uvicorn app.main:app` starts the server on port 8000.

## Testing

`pytest` and `httpx` are regular dependencies (not a separate dev group) so `uv sync` always has what's needed to run `uv run pytest`. If `uv` isn't installed on the host, run tests inside the image instead, e.g.:
`docker compose run --rm -v "$(pwd)/backend/tests:/app/backend/tests" --entrypoint "" app uv run pytest -v`
(the tests directory isn't copied into the built image, so it's bind-mounted in for this)

Tests get an isolated DB via a `client` fixture that `monkeypatch.setenv("DATABASE_PATH", ...)` to a `tmp_path` file before opening `TestClient(app)` as a context manager (the `with` block is what triggers the `lifespan` startup that creates/seeds the DB) — never share `backend/data/pm.db` with tests.

## Known gaps for later parts

- `/api/ai/ask` is a trivial round-trip proof only — no board context, no conversation history, no structured output (Part 9)
