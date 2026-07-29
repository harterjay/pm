# Frontend: Kanban Studio

Pure frontend demo of the Kanban board. State is in-memory only (no backend, no persistence, no auth) — this is the starting point for Parts 3+ of docs/PLAN.md, which wire it to the real backend.

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

## State shape

`BoardData = { columns: Column[]; cards: Record<string, Card> }`. Columns hold ordered `cardIds`; cards are looked up by id from the `cards` map. This normalized shape is what a future backend API/DB schema should mirror.

## Data flow

All mutation logic lives in `KanbanBoard.tsx` and is passed down as callback props — child components never mutate state directly. `moveCard` in `lib/kanban.ts` is a pure function (columns in, columns out) so it's unit-testable without rendering.

## Testing

- Unit/component: `npm run test:unit` (Vitest, jsdom) — `src/lib/kanban.test.ts` covers `moveCard` logic in isolation; `src/components/KanbanBoard.test.tsx` covers rendering, column rename, add/delete card
- E2E: `npm run test:e2e` (Playwright) — `tests/kanban.spec.ts` covers board load, adding a card, and drag-and-drop between columns via raw mouse events (`data-testid="column-*"` / `data-testid="card-*"` are the drag/drop test hooks — keep them when refactoring)
- `npm run test:all` runs both

## Known gaps for later parts

- No auth/login gating (Part 4)
- No API calls — everything is local `useState` (Parts 6-7)
- No AI chat sidebar (Parts 8-10)
- Not yet wired into the Docker/static-export build (Part 2-3)