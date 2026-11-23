import { request } from "./client";
import type { Conversation, ConversationDetail } from "./types";
export const getConversations = (agent?: string) =>
  request<Conversation[]>(
    `/api/conversations${agent ? `?agent=${encodeURIComponent(agent)}` : ""}`,
  );
export const getConversation = (id: string) =>
  request<ConversationDetail>(`/api/conversations/${id}`);
export const renameConversation = (id: string, title: string) =>
  request<Conversation>(`/api/conversations/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
export const deleteConversation = (id: string) =>
  request<void>(`/api/conversations/${id}`, { method: "DELETE" });
