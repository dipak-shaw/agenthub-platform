export interface Agent {
  name: string;
  display_name: string;
  description: string;
  avatar: string;
  avatar_url: string | null;
  accent_color: string;
  tags: string[];
  starter_prompts: string[];
  tools: { native: string; user_toggle: boolean }[];
}
export interface Source {
  index: number;
  title: string;
  url: string;
  snippet: string;
}
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[];
  status: "complete" | "stopped" | "error";
  error_code?: string | null;
  model?: string;
  latency_ms?: number;
  tokens_in?: number;
  tokens_out?: number;
}
export interface Conversation {
  id: string;
  agent_name: string;
  title: string;
  created_at: string;
  updated_at: string;
}
export interface ConversationDetail extends Conversation {
  messages: Message[];
}
export interface Health {
  status: string;
  model_mode: "demo" | "foundry";
  search_provider: string;
  tracing: "on" | "off";
  max_message_chars: number;
}
export type StreamEvent = { run_id: string } & (
  | { type: "run_started"; conversation_id: string; message_id: string }
  | { type: "token"; text: string }
  | { type: "tool_start"; tool: string; input: Record<string, unknown> }
  | { type: "tool_end"; tool: string; sources: Source[] }
  | {
      type: "run_finished";
      status: Message["status"];
      latency_ms: number;
      tokens_in: number;
      tokens_out: number;
    }
  | { type: "error"; code: string; message: string }
);
