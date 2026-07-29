# Backend

FastAPI app, managed with `uv` (see `pyproject.toml`, `package = false` since this is an app, not a library).

## Structure

- `app/main.py` — FastAPI app; `GET /api/health` returns `{"status": "ok"}`; `StaticFiles` mounted at `/` serves `app/static/`
- `app/static/` — checked-in placeholder is the Part 2 hello-world page. In the Docker image, the multi-stage build overwrites this directory with the built Next.js static export (`frontend/out/`, see root `Dockerfile`) — `app/main.py` doesn't care which is present, it just serves whatever is on disk.
- `tests/test_main.py` — integration tests using FastAPI's `TestClient`; `test_root_serves_built_frontend` asserts `/` returns exactly what's in `app/static/index.html`, so it validates static serving regardless of which build (placeholder or real frontend) is present.

## Running

Not run directly with `uvicorn` on the host — built and run via Docker (see root `Dockerfile`, `docker-compose.yml`, `scripts/`). Inside the container, `uv sync` installs dependencies and `uv run uvicorn app.main:app` starts the server on port 8000.

## Testing

`pytest` and `httpx` are regular dependencies (not a separate dev group) so `uv sync` always has what's needed to run `uv run pytest`. If `uv` isn't installed on the host, run tests inside the image instead, e.g.:
`docker compose run --rm -v "$(pwd)/backend/tests:/app/backend/tests" --entrypoint "" app uv run pytest -v`
(the tests directory isn't copied into the built image, so it's bind-mounted in for this)

## Known gaps for later parts

- No auth/session handling (Part 4)
- No database (Parts 5-6)
- No Anthropic/AI endpoints (Parts 8-9)