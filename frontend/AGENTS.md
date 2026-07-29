# Frontend: Kanban Studio

Kanban board UI. As of Part 3, `next.config.ts` sets `output: "export"` and the Docker build compiles this into static HTML/JS served by FastAPI at `/` (see backend/AGENTS.md) — no `next dev`/Node server needed at runtime. As of Part 4, the backend gates `/` and `/login` by session cookie, so all auth/redirect logic lives server-side — the frontend just posts credentials and lets the backend decide where to send the browser next. As of Part 7, board state is no longer local — it's fetched from and mutated through the Part 6 API, backed by the real SQLite DB.

## Stack

- Next.js 16 (App Router), React 19, TypeScript
- Tailwind CSS 4 (via `@tailwindcss/postcss`), styled with CSS variables in `globals.css`
- `@dnd-kit/core` + `@dnd-kit/sortable` for drag and drop
- Vitest + Testing Library for unit/component tests, Playwright for e2e
- `clsx` for conditional class names

## Structure

- `src/app/layout.tsx` — root layout, loads Google fonts (Space Grotesk for display, Manrope for body), sets page metadata
- `src/app/page.tsx` — renders `<KanbanBoard />` at `/`
- `src/app/globals.css` — Tailwind import + the CLAUDE.md color palette as CSS variables (`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`, `--gray-text`)
- `src/lib/kanban.ts` — domain types (`Card`, `Column`, `BoardData`), `initialData` (kept only as canned board data for tests — no longer the runtime seed), and the pure helper `moveCard` (reorder/relocate cards by id, used for both same-column reorder and cross-column drop — still used client-side to compute the optimistic UI state before/independent of the API round-trip)
- `src/components/KanbanBoard.tsx` — top-level stateful component. `board` starts `null` and is populated by `GET /api/board` on mount (loading/error states render in its place until then). Every mutation (`handleDragEnd` → move, `handleRenameColumn`, `handleAddCard`, `handleDeleteCard`) goes through `runMutation`: apply an optimistic local update immediately, fire the API call, replace `board` with the server's authoritative response on success, or roll back to the pre-mutation `board` and show `actionError` (`data-testid="board-error"`) on failure
- `src/components/KanbanColumn.tsx` — droppable column; title `<input>` buffers edits in local `titleDraft` state (so typing doesn't fire a request per keystroke) and only calls `onRename` on blur or Enter; renders cards in a `SortableContext`, embeds `NewCardForm`
- `src/components/KanbanCard.tsx` — sortable/draggable card with a delete button
- `src/components/KanbanCardPreview.tsx` — static (non-interactive) card rendering used inside `DragOverlay` while dragging
- `src/components/NewCardForm.tsx` — toggle button that expands into a title+details form; calls `onAdd` and closes itself on submit
- `src/app/login/page.tsx` — renders `<LoginForm />`; static export produces `out/login.html`
- `src/components/LoginForm.tsx` — username/password form; `POST /api/login`, shows a `data-testid="login-error"` message on failure, calls `onSuccess` (defaults to `window.location.href = "/"`) on success — the `onSuccess` prop exists purely so unit tests can assert without a real navigation
- `KanbanBoard.tsx`'s header also has a "Log out" button: `POST /api/logout` then `window.location.href = "/login"`

## State shape

`BoardData = { columns: Column[]; cards: Record<string, Card> }`, matching `docs/schema.json`'s API response shape exactly (column ids are the DB's `slug`, card ids are `card-<db-id>`) — the frontend does zero id translation.

## Data flow

All mutation logic lives in `KanbanBoard.tsx` and is passed down as callback props — child components never call `fetch` themselves (except `LoginForm`'s login call and the logout button, which are one-shot and don't need board state). `moveCard` in `lib/kanban.ts` stays a pure function (columns in, columns out) so it's unit-testable without rendering, and is reused to compute `handleDragEnd`'s optimistic update.

## Testing

- Unit/component: `npm run test:unit` (Vitest, jsdom) — `src/lib/kanban.test.ts` covers `moveCard` logic in isolation; `src/components/LoginForm.test.tsx` covers the wrong-password and correct-password paths by mocking `fetch` and passing `onSuccess`; `src/components/KanbanBoard.test.tsx` mocks `fetch` with a small in-memory fake server (see `createFakeServer` in that file) so it exercises the real load/mutate/reconcile flow — covers initial load, load failure, rename, add+delete, and a mutation-failure rollback case
- E2E: `npm run test:e2e` (Playwright) — `tests/kanban.spec.ts` covers board load, adding a card, drag-and-drop between columns (`data-testid="column-*"` / `data-testid="card-*"` are the drag/drop test hooks — keep them when refactoring), and a reload-persistence test (add a card, wait for the POST response, `page.reload()`, confirm it's still there — proves persistence through the real backend/DB, not just client state); `tests/login.spec.ts` covers the unauthenticated-redirect, wrong-password, full login→board→logout, and authenticated-visits-to-/login-redirect flows. `tests/auth.ts`'s `loginViaApi` logs in via `page.request.post("/api/login")` (cookies land in the browser context) so `kanban.spec.ts`'s `beforeEach` can skip the UI and get straight to an authenticated board.
- `npm run test:all` runs both — this is the single documented command for the full frontend suite

E2E lifecycle: `playwright.config.ts` uses `globalSetup`/`globalTeardown` (`tests/global-setup.ts` / `tests/global-teardown.ts`), not `webServer`. Setup runs `docker compose down`, deletes `backend/data` (so every run starts from a freshly-seeded DB — otherwise state would accumulate across runs and the reload-persistence/move tests would become order-dependent), then `docker compose up --build -d` and polls `/api/health`. Teardown runs `docker compose down` unconditionally. This also sidesteps the earlier `webServer`-based approach's flaky container-leak-on-Windows problem, since Node's `execSync` control flow doesn't depend on signal propagation to a spawned shell process.

## Known gaps for later parts

- No AI chat sidebar (Parts 8-10)
