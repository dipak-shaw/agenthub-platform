import { Copy, RotateCcw, Check } from "lucide-react";
import { useState } from "react";
import type { Agent, Message } from "../api/types";
import { Avatar } from "./AgentCard";
import Markdown from "./Markdown";
import SourceChips from "./SourceChips";
import ToolStatus from "./ToolStatus";
import { copyText } from "../lib/utils";
export default function ChatMessage({
  message,
  agent,
  streaming = false,
  tool = null,
  onRegenerate,
}: {
  message: Message;
  agent: Agent;
  streaming?: boolean;
  tool?: string | null;
  onRegenerate?: () => void;
}) {
  const [copied, setCopied] = useState(false);
  if (message.role === "user")
    return (
      <article className="user-message" aria-label="Your message">
        <p>{message.content}</p>
      </article>
    );
  return (
    <article className="assistant-message" aria-label="Assistant message">
      <div className="message-heading">
        <Avatar agent={agent} />
        <strong>{agent.display_name}</strong>
      </div>
      <ToolStatus active={tool} searched={message.sources.length > 0} />
      <Markdown text={message.content} sources={message.sources} />
      {streaming && <span aria-label="Generating" className="cursor" />}
      <SourceChips sources={message.sources} />
      {message.status !== "complete" && (
        <p className="muted small">
          {message.status === "stopped"
            ? "Response stopped"
            : "Something went wrong. Try again."}
        </p>
      )}
      {!streaming && (
        <div className="message-actions">
          <button
            className="icon-button"
            aria-label="Copy message"
            onClick={async () => setCopied(await copyText(message.content))}
          >
            {copied ? <Check size={15} /> : <Copy size={15} />}
          </button>
          {onRegenerate && (
            <button
              className="icon-button"
              aria-label={
                message.status === "complete"
                  ? "Regenerate response"
                  : "Retry response"
              }
              onClick={onRegenerate}
            >
              <RotateCcw size={15} />
            </button>
          )}
          <span
            className="small muted"
            title={`${message.tokens_in || 0} input / ${message.tokens_out || 0} output tokens`}
          >
            {message.model}{" "}
            {message.latency_ms
              ? `· ${(message.latency_ms / 1000).toFixed(1)}s`
              : ""}
          </span>
        </div>
      )}
    </article>
  );
}
