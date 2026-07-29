"use client";

import { useState, type FormEvent } from "react";
import type { BoardData } from "@/lib/kanban";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ChatSidebarProps = {
  board: BoardData;
  onBoardUpdate: (board: BoardData) => void;
};

export const ChatSidebar = ({ board, onBoardUpdate }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async (event: FormEvent) => {
    event.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    const history = messages;
    setMessages([...history, { role: "user", content: text }]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const response = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ board, message: text, history }),
      });

      if (!response.ok) {
        throw new Error("Request failed");
      }

      const data = (await response.json()) as { reply: string; board: BoardData };
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
      onBoardUpdate(data.board);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSending(false);
    }
  };

  return (
    <aside className="flex w-full flex-col gap-4 self-start rounded-[32px] border border-[var(--stroke)] bg-white/80 p-6 shadow-[var(--shadow)] backdrop-blur lg:w-96">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
          AI Assistant
        </p>
        <h2 className="mt-2 font-display text-xl font-semibold text-[var(--navy-dark)]">
          Chat with the assistant
        </h2>
      </div>

      <div
        data-testid="chat-messages"
        className="flex max-h-[50vh] flex-1 flex-col gap-3 overflow-y-auto"
      >
        {messages.length === 0 && (
          <p className="text-sm leading-6 text-[var(--gray-text)]">
            Ask me to add, edit, move, or delete cards — or just ask a question
            about the board.
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            data-testid={`chat-message-${message.role}`}
            className={
              message.role === "user"
                ? "self-end rounded-2xl bg-[var(--secondary-purple)] px-4 py-2 text-sm text-white"
                : "self-start rounded-2xl bg-[var(--surface)] px-4 py-2 text-sm text-[var(--navy-dark)]"
            }
          >
            {message.content}
          </div>
        ))}
        {sending && (
          <p className="text-sm text-[var(--gray-text)]" data-testid="chat-thinking">
            Thinking…
          </p>
        )}
      </div>

      {error && (
        <p
          role="alert"
          data-testid="chat-error"
          className="text-sm font-semibold text-red-600"
        >
          {error}
        </p>
      )}

      <form onSubmit={handleSend} className="flex items-center gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask the AI..."
          disabled={sending}
          data-testid="chat-input"
          className="flex-1 rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          data-testid="chat-send"
          className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110 disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </aside>
  );
};
