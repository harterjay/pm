import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData, type BoardData } from "@/lib/kanban";

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

const cloneBoard = (board: BoardData): BoardData =>
  JSON.parse(JSON.stringify(board));

// A minimal in-memory stand-in for the Part 6 API so these tests exercise
// the real fetch/optimistic-update/reconcile flow in KanbanBoard, not just
// a static render.
const createFakeServer = (initial: BoardData) => {
  let board = cloneBoard(initial);
  let nextId = 100;

  const ok = (): Response =>
    ({ ok: true, json: async () => cloneBoard(board) }) as Response;

  return vi.fn(async (url: string, init?: RequestInit): Promise<Response> => {
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(init.body as string) : undefined;

    if (method === "GET" && url === "/api/board") {
      return ok();
    }

    const renameMatch = url.match(/^\/api\/board\/columns\/([^/]+)$/);
    if (method === "PATCH" && renameMatch) {
      const [, columnId] = renameMatch;
      board = {
        ...board,
        columns: board.columns.map((column) =>
          column.id === columnId ? { ...column, title: body.title } : column
        ),
      };
      return ok();
    }

    const addMatch = url.match(/^\/api\/board\/columns\/([^/]+)\/cards$/);
    if (method === "POST" && addMatch) {
      const [, columnId] = addMatch;
      const id = `card-${nextId++}`;
      board = {
        ...board,
        cards: {
          ...board.cards,
          [id]: { id, title: body.title, details: body.details || "No details yet." },
        },
        columns: board.columns.map((column) =>
          column.id === columnId
            ? { ...column, cardIds: [...column.cardIds, id] }
            : column
        ),
      };
      return ok();
    }

    const deleteMatch = url.match(/^\/api\/board\/cards\/([^/]+)$/);
    if (method === "DELETE" && deleteMatch) {
      const [, cardId] = deleteMatch;
      const { [cardId]: _removed, ...remainingCards } = board.cards;
      board = {
        ...board,
        cards: remainingCards,
        columns: board.columns.map((column) => ({
          ...column,
          cardIds: column.cardIds.filter((id) => id !== cardId),
        })),
      };
      return ok();
    }

    throw new Error(`Unhandled request in test fake server: ${method} ${url}`);
  });
};

describe("KanbanBoard", () => {
  it("loads and renders five columns from the API", async () => {
    vi.stubGlobal("fetch", createFakeServer(initialData));
    render(<KanbanBoard />);

    expect(screen.getByText(/loading board/i)).toBeInTheDocument();
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("shows an error when the initial load fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false }) as Response)
    );
    render(<KanbanBoard />);

    expect(
      await screen.findByText(/couldn't load the board/i)
    ).toBeInTheDocument();
  });

  it("renames a column", async () => {
    vi.stubGlobal("fetch", createFakeServer(initialData));
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);

    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    await userEvent.tab();

    await waitFor(() => expect(input).toHaveValue("New Name"));
  });

  it("adds and removes a card", async () => {
    vi.stubGlobal("fetch", createFakeServer(initialData));
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);

    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    await waitFor(() =>
      expect(within(column).getByText("New card")).toBeInTheDocument()
    );

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    await waitFor(() =>
      expect(within(column).queryByText("New card")).not.toBeInTheDocument()
    );
  });

  it("shows an error and rolls back the optimistic update when a mutation fails", async () => {
    const fetchMock = createFakeServer(initialData);
    vi.stubGlobal("fetch", fetchMock);
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);

    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title") as HTMLInputElement;
    const originalTitle = input.value;

    fetchMock.mockImplementationOnce(async () => ({ ok: false }) as Response);

    await userEvent.clear(input);
    await userEvent.type(input, "Will fail");
    await userEvent.tab();

    expect(await screen.findByTestId("board-error")).toHaveTextContent(
      "Something went wrong. Please try again."
    );
    await waitFor(() => expect(input).toHaveValue(originalTitle));
  });
});
