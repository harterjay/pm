"use client";

import { useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { ChatSidebar } from "@/components/ChatSidebar";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { moveCard, type BoardData } from "@/lib/kanban";

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/board")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load board");
        }
        return response.json() as Promise<BoardData>;
      })
      .then((data) => {
        if (!cancelled) {
          setBoard(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setLoadError("Couldn't load the board. Try refreshing the page.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board]);

  const runMutation = async (
    optimisticBoard: BoardData,
    request: () => Promise<Response>
  ) => {
    const previousBoard = board;
    setBoard(optimisticBoard);
    setActionError(null);
    try {
      const response = await request();
      if (!response.ok) {
        throw new Error("Request failed");
      }
      const nextBoard = (await response.json()) as BoardData;
      setBoard(nextBoard);
    } catch {
      setBoard(previousBoard);
      setActionError("Something went wrong. Please try again.");
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!board || !over || active.id === over.id) {
      return;
    }

    const activeId = active.id as string;
    const overId = over.id as string;

    const isOverColumn = board.columns.some((column) => column.id === overId);
    const targetColumn = isOverColumn
      ? board.columns.find((column) => column.id === overId)
      : board.columns.find((column) => column.cardIds.includes(overId));

    if (!targetColumn) {
      return;
    }

    const remainingIds = targetColumn.cardIds.filter((id) => id !== activeId);
    const overIndex = remainingIds.indexOf(overId);
    const position = isOverColumn || overIndex === -1 ? remainingIds.length : overIndex;

    const optimisticBoard: BoardData = {
      ...board,
      columns: moveCard(board.columns, activeId, overId),
    };

    runMutation(optimisticBoard, () =>
      fetch(`/api/board/cards/${activeId}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ columnId: targetColumn.id, position }),
      })
    );
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    if (!board) return;
    const optimisticBoard: BoardData = {
      ...board,
      columns: board.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    };
    runMutation(optimisticBoard, () =>
      fetch(`/api/board/columns/${columnId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      })
    );
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    if (!board) return;
    // Optimistic UI needs a placeholder id; the server assigns the real one
    // and the mutation reconciles it away on success.
    const placeholderId = `pending-${Date.now()}`;
    const optimisticBoard: BoardData = {
      ...board,
      cards: {
        ...board.cards,
        [placeholderId]: {
          id: placeholderId,
          title,
          details: details || "No details yet.",
        },
      },
      columns: board.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, placeholderId] }
          : column
      ),
    };

    runMutation(optimisticBoard, () =>
      fetch(`/api/board/columns/${columnId}/cards`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, details }),
      })
    );
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    if (!board) return;
    const optimisticBoard: BoardData = {
      ...board,
      cards: Object.fromEntries(
        Object.entries(board.cards).filter(([id]) => id !== cardId)
      ),
      columns: board.columns.map((column) =>
        column.id === columnId
          ? {
              ...column,
              cardIds: column.cardIds.filter((id) => id !== cardId),
            }
          : column
      ),
    };

    runMutation(optimisticBoard, () =>
      fetch(`/api/board/cards/${cardId}`, { method: "DELETE" })
    );
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  const handleLogout = async () => {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "/login";
  };

  if (loadError) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6 text-center">
        <p className="text-sm font-semibold text-[var(--navy-dark)]">{loadError}</p>
      </div>
    );
  }

  if (!board) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm font-semibold text-[var(--gray-text)]">Loading board…</p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="h-fit rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)] transition hover:border-[var(--secondary-purple)] hover:text-[var(--secondary-purple)]"
            >
              Log out
            </button>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
          {actionError && (
            <p
              role="alert"
              data-testid="board-error"
              className="text-sm font-semibold text-red-600"
            >
              {actionError}
            </p>
          )}
        </header>

        <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <section className="grid flex-1 gap-6 lg:grid-cols-5">
              {board.columns.map((column) => (
                <KanbanColumn
                  key={column.id}
                  column={column}
                  cards={column.cardIds.map((cardId) => board.cards[cardId])}
                  onRename={handleRenameColumn}
                  onAddCard={handleAddCard}
                  onDeleteCard={handleDeleteCard}
                />
              ))}
            </section>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[260px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>

          <ChatSidebar board={board} onBoardUpdate={setBoard} />
        </div>
      </main>
    </div>
  );
};
