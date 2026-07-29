# Frontend: Kanban Studio

Kanban board UI. Board state is still in-memory only (no persistence) — that's wired up in Parts 6-7 of docs/PLAN.md. As of Part 3, `next.config.ts` sets `output: "export"` and the Docker build compiles this into static HTML/JS served by FastAPI at `/` (see backend/AGENTS.md) — no `next dev`/Node server needed at runtime. As of Part 4, the backend gates `/` and `/login` by session cookie, so all auth/redirect logic lives server-side — the frontend just posts credentials and lets the backend decide where to send the browser next.

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
- `src/lib/kanban.ts` — domain types (`Card`, `Column`, `BoardData`), hardcoded `initialData` (5 columns, 8 seed cards), and pure helpers: `moveCard` (reorder/relocate cards by id, used for both same-column reorder and cross-column drop) and `createId` (client-side id generator)
- `src/components/KanbanBoard.tsx` — top-level stateful component; owns `board` state via `useState(initialData)`, wires up `DndContext`, and implements all mutations (`handleDragEnd` → `moveCard`, `handleRenameColumn`, `handleAddCard`, `handleDeleteCard`)
- `src/components/KanbanColumn.tsx` — droppable column; editable title `<input>`, renders cards in a `SortableContext`, embeds `NewCardForm`
- `src/components/KanbanCard.tsx` — sortable/draggable card with a delete button
- `src/components/KanbanCardPreview.tsx` — static (non-interactive) card rendering used inside `DragOverlay` while dragging
- `src/components/NewCardForm.tsx` — toggle button that expands into a title+details form; calls `onAdd` and closes itself on submit
- `src/app/login/page.tsx` — renders `<LoginForm />`; static export produces `out/login.html`
- `src/components/LoginForm.tsx` — username/password form; `POST /api/login`, shows a `data-testid="login-error"` message on failure, calls `onSuccess` (defaults to `window.location.href = "/"`) on success — the `onSuccess` prop exists purely so unit tests can assert without a real navigation
- `KanbanBoard.tsx`'s header also has a "Log out" button: `POST /api/logout` then `window.location.href = "/login"`

## State shape

`BoardData = { columns: Column[]; cards: Record<string, Card> }`. Columns hold ordered `cardIds`; cards are looked up by id from the `cards` map. This normalized shape is what a future backend API/DB schema should mirror.

## Data flow

All mutation logic lives in `KanbanBoard.tsx` and is passed down as callback props — child components never mutate state directly. `moveCard` in `lib/kanban.ts` is a pure function (columns in, columns out) so it's unit-testable without rendering.

## Testing

- Unit/component: `npm run test:unit` (Vitest, jsdom) — `src/lib/kanban.test.ts` covers `moveCard` logic in isolation; `src/components/KanbanBoard.test.tsx` covers rendering, column rename, add/delete card; `src/components/LoginForm.test.tsx` covers the wrong-password and correct-password paths by mocking `fetch` and passing `onSuccess`
- E2E: `npm run test:e2e` (Playwright) — `tests/kanban.spec.ts` covers board load, adding a card, and drag-and-drop between columns via raw mouse events (`data-testid="column-*"` / `data-testid="card-*"` are the drag/drop test hooks — keep them when refactoring); `tests/login.spec.ts` covers the unauthenticated-redirect, wrong-password, full login→board→logout, and authenticated-visits-to-/login-redirect flows through the real UI. `tests/auth.ts`'s `loginViaApi` logs in via `page.request.post("/api/login")` (cookies land in the browser context) so `kanban.spec.ts`'s `beforeEach` can skip the UI and get straight to an authenticated board. Runs against the real Dockerized build, not `next dev`: `playwright.config.ts`'s `webServer` runs `docker compose up --build` (`cwd: ".."`) and `baseURL` points at `http://127.0.0.1:8000`.
- `npm run test:all` runs both — this is the single documented command for the full frontend suite

Known issue: on Windows, Playwright's `webServer` teardown doesn't reliably stop the `docker compose up` process it spawns, so a container can be left running after `npm run test:e2e`. Run `docker compose down` (or `scripts/stop.ps1`) afterward if `docker ps` still shows `pm-app-1`.

## Known gaps for later parts

- No API calls for board data — everything is local `useState` (Parts 6-7)
- No AI chat sidebar (Parts 8-10)