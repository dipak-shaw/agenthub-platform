import type { Conversation } from "../api/types";
export function groupConversations(
  items: Conversation[],
  now = new Date(),
): [string, Conversation[]][] {
  const start = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  ).getTime();
  const groups: Record<string, Conversation[]> = {
    Today: [],
    Yesterday: [],
    "Previous 7 days": [],
    Older: [],
  };
  for (const item of items) {
    const days = (start - new Date(item.updated_at).getTime()) / 86400000;
    const label =
      days <= 0
        ? "Today"
        : days <= 1
          ? "Yesterday"
          : days < 7
            ? "Previous 7 days"
            : "Older";
    groups[label].push(item);
  }
  return Object.entries(groups).filter(([, rows]) => rows.length);
}
