import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test, vi } from "vitest";
import AgentCard from "../src/components/AgentCard";
import ChatMessage from "../src/components/ChatMessage";
import Composer from "../src/components/Composer";
import Sidebar from "../src/components/Sidebar";
import { groupConversations } from "../src/lib/date";
import { agent } from "./fixtures";

test("agent card links to chat and describes tools", () => {
  render(
    <MemoryRouter>
      <AgentCard agent={agent} />
    </MemoryRouter>,
  );
  expect(screen.getByRole("link")).toHaveAttribute(
    "href",
    "/agents/search-bot",
  );
  expect(screen.getByLabelText("Web search available")).toBeInTheDocument();
});

test("assistant renders markdown, safe citations, and code", () => {
  render(
    <ChatMessage
      agent={agent}
      message={{
        id: "1",
        role: "assistant",
        content:
          "## Findings\n\nEvidence [1]\n\n```python\nprint('hello')\n```",
        status: "complete",
        sources: [
          {
            index: 1,
            title: "Fictional source",
            url: "https://fictional.example",
            snippet: "Notes",
          },
        ],
      }}
    />,
  );
  expect(screen.getByRole("heading", { name: "Findings" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "1" })).toHaveAttribute(
    "href",
    "https://fictional.example",
  );
  expect(screen.getByRole("button", { name: "Copy code" })).toBeInTheDocument();
  expect(screen.getByLabelText("Sources")).toHaveTextContent(
    "Fictional source",
  );
});

test("composer Enter sends, Shift+Enter does not, Stop works", () => {
  const send = vi.fn(),
    stop = vi.fn();
  const props = {
    busy: false,
    searchToggle: true,
    enabled: true,
    onToggle: vi.fn(),
    onSend: send,
    onStop: stop,
  };
  const view = render(<Composer {...props} />);
  const input = screen.getByRole("textbox", { name: "Message" });
  fireEvent.change(input, { target: { value: "hello" } });
  fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
  expect(send).not.toHaveBeenCalled();
  fireEvent.keyDown(input, { key: "Enter" });
  expect(send).toHaveBeenCalledWith("hello");
  view.rerender(<Composer {...props} busy />);
  fireEvent.click(screen.getByRole("button", { name: "Stop response" }));
  expect(stop).toHaveBeenCalledOnce();
});

test("sidebar date groups use local midnight and expose rename/delete actions", () => {
  const now = new Date(2025, 5, 15, 12);
  const day = (n: number) => new Date(2025, 5, 15 - n, 10).toISOString();
  const chats = [0, 1, 3, 10].map((n) => ({
    id: String(n),
    agent_name: "search-bot",
    title: `Chat ${n}`,
    created_at: day(n),
    updated_at: day(n),
  }));
  expect(groupConversations(chats, now).map(([label]) => label)).toEqual([
    "Today",
    "Yesterday",
    "Previous 7 days",
    "Older",
  ]);
  render(
    <MemoryRouter>
      <Sidebar
        agent={agent}
        conversations={chats}
        open
        current="0"
        onClose={vi.fn()}
        onNew={vi.fn()}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        busy={false}
      />
    </MemoryRouter>,
  );
  expect(screen.getByRole("button", { name: /New chat/ })).toBeInTheDocument();
  expect(screen.getByLabelText("Actions for Chat 0")).toBeInTheDocument();
});
