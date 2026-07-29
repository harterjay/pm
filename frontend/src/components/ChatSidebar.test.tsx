import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatSidebar } from "@/components/ChatSidebar";
import { initialData } from "@/lib/kanban";

describe("ChatSidebar", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("shows an empty-state hint when there is no history", () => {
    render(<ChatSidebar board={initialData} onBoardUpdate={vi.fn()} />);
    expect(screen.getByText(/ask me to add, edit, move, or delete/i)).toBeInTheDocument();
  });

  it("sends a message, renders the reply, and refreshes the board", async () => {
    const updatedBoard = { ...initialData, columns: [...initialData.columns] };
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ reply: "Done!", board: updatedBoard }),
    });
    const onBoardUpdate = vi.fn();

    render(<ChatSidebar board={initialData} onBoardUpdate={onBoardUpdate} />);
    await userEvent.type(screen.getByTestId("chat-input"), "Move card-1 to Done");
    await userEvent.click(screen.getByTestId("chat-send"));

    expect(await screen.findByTestId("chat-message-assistant")).toHaveTextContent("Done!");
    expect(screen.getByTestId("chat-message-user")).toHaveTextContent("Move card-1 to Done");
    expect(onBoardUpdate).toHaveBeenCalledWith(updatedBoard);

    expect(fetch).toHaveBeenCalledWith(
      "/api/ai/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          board: initialData,
          message: "Move card-1 to Done",
          history: [],
        }),
      })
    );
  });

  it("shows an error and keeps onBoardUpdate untouched when the request fails", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({ ok: false });
    const onBoardUpdate = vi.fn();

    render(<ChatSidebar board={initialData} onBoardUpdate={onBoardUpdate} />);
    await userEvent.type(screen.getByTestId("chat-input"), "hello");
    await userEvent.click(screen.getByTestId("chat-send"));

    expect(await screen.findByTestId("chat-error")).toHaveTextContent(
      "Something went wrong. Please try again."
    );
    expect(onBoardUpdate).not.toHaveBeenCalled();
  });
});
