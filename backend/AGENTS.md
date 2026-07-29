# Backend

FastAPI app, managed with `uv` (see `pyproject.toml`, `package = false` since this is an app, not a library).

## Structure

- `app/main.py` — FastAPI app; `GET /api/health` returns `{"status": "ok"}`; `StaticFiles` mounted at `/` serves `app/static/`
- `app/static/index.html` — hello-world page (Part 2 placeholder), fetches `/api/health` on load and displays the result. Part 3 replaces this directory's contents with the built Next.js static export.

## Running

Not run directly with `uvicorn` on the host — built and run via Docker (see root `Dockerfile`, `docker-compose.yml`, `scripts/`). Inside the container, `uv sync` installs dependencies and `uv run uvicorn app.main:app` starts the server on port 8000.

## Known gaps for later parts

- No frontend static export served yet (Part 3)
- No auth/session handling (Part 4)
- No database (Parts 5-6)
- No Anthropic/AI endpoints (Parts 8-9)