import type { StreamEvent } from "./types";
export interface ChatBody {
  conversation_id?: string;
  message: string;
  web_search_enabled: boolean;
  regenerate?: boolean;
}

/** Decode SSE incrementally, including UTF-8 characters and frames split across packets. */
export async function readEvents(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finished = false;
  const frames = () => {
    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const data = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())
        .join("\n");
      if (data) {
        const event = JSON.parse(data) as StreamEvent;
        if (event.type === "run_finished") finished = true;
        onEvent(event);
      }
    }
  };
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
      frames();
    }
    buffer += decoder.decode();
    frames();
    if (!finished)
      throw new Error(
        "The response stream ended unexpectedly. You can retry the saved turn.",
      );
  } finally {
    reader.releaseLock();
  }
}
export async function streamChat(
  name: string,
  body: ChatBody,
  signal: AbortSignal,
  onEvent: (event: StreamEvent) => void,
) {
  const response = await fetch(`/api/agents/${encodeURIComponent(name)}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || error.detail || "Unable to start chat");
  }
  if (!response.body)
    throw new Error("Streaming is unavailable in this browser");
  await readEvents(response.body, onEvent);
}
