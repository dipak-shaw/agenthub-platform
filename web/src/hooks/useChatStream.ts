import { useCallback, useEffect, useRef, useState } from "react";
import { streamChat, type ChatBody } from "../api/stream";
import { request } from "../api/client";
import type { Message } from "../api/types";

export function useChatStream() {
  const [busy, setBusy] = useState(false);
  const [reply, setReply] = useState<Message | null>(null);
  const [tool, setTool] = useState<string | null>(null);
  const [error, setError] = useState("");
  const controller = useRef<AbortController>();
  const run = useRef<string>();
  useEffect(() => () => controller.current?.abort(), []);
  const start = useCallback(
    async (agent: string, body: ChatBody, onStarted: (id: string) => void) => {
      if (controller.current) return;
      const abort = new AbortController();
      controller.current = abort;
      run.current = undefined;
      setBusy(true);
      setError("");
      setReply({
        id: "pending",
        role: "assistant",
        content: "",
        sources: [],
        status: "complete",
      });
      try {
        await streamChat(agent, body, abort.signal, (event) => {
          run.current = event.run_id;
          if (event.type === "run_started") {
            onStarted(event.conversation_id);
            setReply((value) => value && { ...value, id: event.message_id });
          }
          if (event.type === "token")
            setReply(
              (value) =>
                value && { ...value, content: value.content + event.text },
            );
          if (event.type === "tool_start")
            setTool(
              event.tool === "web_search"
                ? `Searching the web for “${String(event.input.query || "sources")}”…`
                : "Reading page…",
            );
          if (event.type === "tool_end") {
            setTool(null);
            setReply(
              (value) =>
                value && {
                  ...value,
                  sources: [
                    ...new Map(
                      [...value.sources, ...event.sources].map((source) => [
                        source.url,
                        source,
                      ]),
                    ).values(),
                  ],
                },
            );
          }
          if (event.type === "error") {
            if (event.code !== "run_cancelled") setError(event.message);
            setReply((value) => value && { ...value, error_code: event.code });
          }
          if (event.type === "run_finished")
            setReply(
              (value) =>
                value && {
                  ...value,
                  status: event.status,
                  latency_ms: event.latency_ms,
                  tokens_in: event.tokens_in,
                  tokens_out: event.tokens_out,
                },
            );
        });
      } catch (cause) {
        if (!abort.signal.aborted) {
          setError(
            cause instanceof Error ? cause.message : "Connection failed",
          );
          setReply((value) => value && { ...value, status: "error" });
        }
      } finally {
        controller.current = undefined;
        run.current = undefined;
        setBusy(false);
        setTool(null);
      }
    },
    [],
  );
  const stop = useCallback(async () => {
    if (run.current) {
      try {
        await request(`/api/runs/${run.current}/stop`, { method: "POST" });
      } catch {
        /* Completion can win the stop race. */
      }
    } else controller.current?.abort();
  }, []);
  const clear = useCallback(() => {
    setReply(null);
    setError("");
  }, []);
  return { busy, reply, tool, error, start, stop, clear };
}
