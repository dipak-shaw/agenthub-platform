import { act, renderHook } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { readEvents } from "../src/api/stream";
import { useChatStream } from "../src/hooks/useChatStream";
import type { StreamEvent } from "../src/api/types";
const encode = new TextEncoder();
function response(events: StreamEvent[]) {
  const data = events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join("");
  return new ReadableStream<Uint8Array>({
    start(controller) {
      const bytes = encode.encode(data);
      for (let i = 0; i < bytes.length; i += 3)
        controller.enqueue(bytes.slice(i, i + 3));
      controller.close();
    },
  });
}
const events: StreamEvent[] = [
  { type: "run_started", run_id: "r", conversation_id: "c", message_id: "m" },
  {
    type: "tool_start",
    run_id: "r",
    tool: "web_search",
    input: { query: "test" },
  },
  {
    type: "tool_end",
    run_id: "r",
    tool: "web_search",
    sources: [
      {
        index: 1,
        url: "https://example.test",
        title: "Example",
        snippet: "Notes",
      },
    ],
  },
  { type: "token", run_id: "r", text: "Hello 🌿" },
  {
    type: "run_finished",
    run_id: "r",
    status: "complete",
    latency_ms: 30,
    tokens_in: 1,
    tokens_out: 2,
  },
];

test("SSE parser preserves split UTF-8 frames", async () => {
  const received: StreamEvent[] = [];
  await readEvents(response(events), (e) => received.push(e));
  expect(received).toEqual(events);
});
test("truncated stream fails explicitly", async () => {
  await expect(
    readEvents(response(events.slice(0, -1)), () => {}),
  ).rejects.toThrow("unexpectedly");
});
test("chat hook consumes events and retains sources and metrics", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(response(events))),
  );
  const { result } = renderHook(useChatStream);
  const started = vi.fn();
  await act(async () => {
    await result.current.start(
      "bot",
      { message: "test", web_search_enabled: true },
      started,
    );
  });
  expect(started).toHaveBeenCalledWith("c");
  expect(result.current.busy).toBe(false);
  expect(result.current.reply?.content).toBe("Hello 🌿");
  expect(result.current.reply?.sources).toHaveLength(1);
  expect(result.current.reply?.tokens_out).toBe(2);
});
test("chat hook handles persisted errors", async () => {
  const failure: StreamEvent[] = [
    events[0],
    { type: "error", run_id: "r", code: "run_timeout", message: "Timed out" },
    {
      ...events[4],
      type: "run_finished",
      status: "error",
      latency_ms: 3,
      tokens_in: 0,
      tokens_out: 0,
    },
  ];
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(response(failure))),
  );
  const { result } = renderHook(useChatStream);
  await act(async () => {
    await result.current.start(
      "bot",
      { message: "test", web_search_enabled: false },
      () => {},
    );
  });
  expect(result.current.error).toBe("Timed out");
  expect(result.current.reply?.status).toBe("error");
});
