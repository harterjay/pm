# Database approach

See `docs/schema.json` for the actual table/column definitions and seed data. This document covers the operational side: where the file lives, how it gets created, and how ids map to what the frontend already expects.

## Engine and file location

SQLite, accessed with Python's stdlib `sqlite3` (no ORM — four small tables don't need one).

The file lives at `backend/data/pm.db`, outside the `app/` package (so it's never accidentally baked into the Docker image alongside application code, and `app/` stays purely "code"). `docker-compose.yml` mounts a volume onto that path so the database survives `docker compose down`/`up` cycles instead of resetting on every container recreation. `backend/data/` is gitignored — the file is runtime state, not source.

## Creation and migration strategy

No migration framework (Alembic, etc.) — that's overkill for four tables that aren't expected to change shape often. Instead, on every app startup:

1. Run `CREATE TABLE IF NOT EXISTS` for all four tables (idempotent — safe whether the file is brand new or already exists).
2. `PRAGMA foreign_keys = ON` (SQLite has foreign keys off by default; needed for the `ON DELETE CASCADE` behavior in the schema).
3. If the `users` table is empty, insert the seed data from `docs/schema.json`'s `seed` block (one user, one board, the 5 fixed columns, the 8 demo cards) — this is the "first run" case. If `users` already has rows, skip seeding entirely.

If a real schema change is ever needed later, the plan is a hand-written one-off script, not a migration system — consistent with "don't build for hypothetical future requirements."

## Id mapping to BoardData

The frontend's `BoardData` shape (`frontend/src/lib/kanban.ts`) uses string ids for columns and cards. Rather than add a translation layer, the seed data is chosen so the DB's own ids already match:

- **Column id** = `columns.slug` directly (`col-backlog`, `col-discovery`, `col-progress`, `col-review`, `col-done` — identical to today's hardcoded frontend seed ids). The API never needs to invent or translate a column id.
- **Card id** = `f"card-{cards.id}"`, and because the seed cards are inserted in the same order as today's `initialData`, autoincrement hands out 1..8 in the same order — so the ids come out as `card-1`..`card-8`, exactly what the existing e2e tests (`kanban.spec.ts`, `card-card-1` etc. testids) already assume. No test changes needed when Part 6/7 wire up the real API.

`title` is the only renamable field on a column; `slug` never changes after seeding, which is what makes it safe for backend/AI logic to key off later even after a user renames "Done" to something else.

## Testing implications for Part 6

Backend tests need a fresh, isolated DB per test rather than sharing `backend/data/pm.db`. The plan is a `DATABASE_PATH` environment variable (defaulting to `backend/data/pm.db`) that tests override to a temp file (or `:memory:`) per test — deferred to Part 6's implementation, called out here so the schema/creation logic is written with that override in mind from the start.
