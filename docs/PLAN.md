# High level steps for project

See CLAUDE.md for business requirements, technical decisions, and coding standards. See frontend/AGENTS.md for the existing frontend starting point.

## Part 1: Plan

- [x] Enrich this document with substeps, tests, and success criteria per part
- [x] Create frontend/AGENTS.md describing the existing frontend code
- [x] User reviews and approves this plan before Part 2 starts

**Success criteria:** user has explicitly signed off on this plan.

## Part 2: Scaffolding

- [x] Create `backend/` FastAPI app (`uv` for dependency management, `pyproject.toml`)
- [x] Backend serves a static "hello world" HTML page at `/`
- [x] Backend exposes one example API route (e.g. `GET /api/health`) that the hello-world page calls to prove client-to-API wiring works
- [x] `Dockerfile` that builds and runs the backend with `uv`
- [x] `docker-compose.yml` (or equivalent) to run the container locally
- [x] `scripts/start.sh`, `scripts/start.ps1`, `scripts/stop.sh`, `scripts/stop.ps1` for Mac, PC, Linux
- [x] Update `scripts/AGENTS.md` and `backend/AGENTS.md` describing what was set up

**Tests:**
- Manual: `scripts/start` brings up the container; visiting `/` shows the hello-world page and its on-page API call succeeds
- `scripts/stop` cleanly tears the container down

**Success criteria:** a fresh clone can run the start script and see a working hello-world page making a live API call, entirely inside Docker.

## Part 3: Add in Frontend

- [x] Configure Next.js for static export (`output: "export"` or equivalent)
- [x] Update Dockerfile/build so the backend serves the built frontend static assets at `/`
- [x] Confirm the existing Kanban demo (frontend/AGENTS.md) renders unchanged when served by FastAPI instead of `next dev`
- [x] Wire frontend unit tests (`npm run test:unit`) and e2e tests (`npm run test:e2e`) into a single documented command, run against the Dockerized build
- [x] Add a backend integration test that asserts `/` returns the built frontend HTML

**Tests:**
- `npm run test:all` passes
- Backend integration test confirms static asset serving
- Manual: `scripts/start`, visit `/`, see the same Kanban demo as `next dev`, drag/drop and add/delete cards still work

**Success criteria:** the full demo Kanban UI loads at `/` when running only via Docker/FastAPI (no `next dev` needed), with all existing frontend tests still green.

## Part 4: Add in a fake user sign in experience

- [x] Login page/form requiring hardcoded `user` / `password`
- [x] Redirect unauthenticated visits to `/` to the login page; redirect authenticated visits away from login
- [x] Session handling (e.g. cookie or token) issued by backend on successful login
- [x] Logout action that clears the session and returns to login
- [x] Frontend unit tests for login form validation (wrong password rejected, correct password accepted)
- [x] E2E test: cannot see Kanban without logging in; can log in, see Kanban, log out, redirected to login
- [x] Backend unit tests for the login/logout/session-check endpoints

**Success criteria:** visiting `/` with no session shows login; correct hardcoded credentials grant access to the Kanban board; logout revokes access; all new tests green alongside existing suite.

## Part 5: Database modeling

- [x] Propose a normalized schema (mirroring `BoardData` in frontend/src/lib/kanban.ts: users, boards, columns, cards) as JSON in `docs/`
- [x] Document the database approach (SQLite, file location, migration/creation strategy) in `docs/`
- [x] Get explicit user sign-off on the schema before Part 6 starts

**Success criteria:** user has approved the schema document.

## Part 6: Backend

- [x] SQLite database created automatically on first run if it doesn't exist, seeded with the demo board for the hardcoded user
- [x] API routes: get board, rename column, add card, edit card, delete card, move card — scoped to the signed-in user
- [x] Backend unit tests for every route, including edge cases (invalid ids, empty titles, moving to a nonexistent column)
- [x] Tests confirm the DB file is created fresh when missing and reused when present

**Success criteria:** full CRUD + move on the Kanban is possible via API alone (e.g. via curl/pytest), independent of the frontend, backed by a real SQLite file, with thorough passing tests.

## Part 7: Frontend + Backend

- [x] Replace in-memory `useState(initialData)` in `KanbanBoard.tsx` with calls to the Part 6 API (fetch on load, mutate via API on rename/add/edit/delete/move)
- [x] Loading and error states for API calls
- [x] Update/add frontend tests to mock the API and cover success + failure paths
- [x] E2E tests updated to run against the real backend (no more purely client-side state) and confirm state persists across a page reload

**Success criteria:** reloading the page preserves board state (proves persistence through the backend/DB); all frontend, backend, and e2e tests green.

## Part 8: AI connectivity

- [ ] Backend endpoint that calls Anthropic (key from `.env`, model per CLAUDE.md) with a trivial prompt
- [ ] Test: send "what is 2+2?" through the endpoint, assert the response contains "4"
- [ ] Confirm failure mode when the API key is missing/invalid is handled without crashing the server

**Success criteria:** a passing test proves a live round-trip call to Anthropic works end-to-end from the backend.

## Part 9: Kanban-aware AI with Structured Outputs

- [ ] Extend the AI endpoint to accept: current board JSON, user's message, conversation history
- [ ] Define a Structured Output schema: a text reply to the user, plus an optional Kanban update (create/edit/move/delete cards, rename columns)
- [ ] Apply the optional Kanban update to the database when present
- [ ] Backend tests: AI asked to answer a question only (no board change) → board unchanged; AI asked to move/create/edit a card → board updated correctly and matches the structured update returned
- [ ] Handle/test malformed or partial structured responses gracefully

**Success criteria:** a conversational request like "move the roadmap card to Done" results in a correct DB update and a sensible chat reply, verified by tests without needing the UI.

## Part 10: AI chat sidebar in the UI

- [ ] Sidebar chat component: message history, input box, send button, styled per CLAUDE.md color scheme
- [ ] Sidebar calls the Part 9 endpoint with the current board state and message history
- [ ] When the response includes a Kanban update, refresh the board view automatically without a full page reload
- [ ] Frontend unit tests for the chat component (renders history, sends message, handles board-refresh callback)
- [ ] E2E test: ask the AI to move/add a card via chat, confirm the board visibly updates

**Success criteria:** a user can chat in the sidebar, ask for a Kanban change in plain language, and see the board update live, with tests covering both the chat UI and the resulting board mutation.