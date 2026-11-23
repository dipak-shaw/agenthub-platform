import type { Agent } from "../src/api/types";
export const agent: Agent = {
  name: "search-bot",
  display_name: "Search Bot",
  description: "A fictional search assistant",
  avatar: "🔎",
  avatar_url: null,
  accent_color: "#6366f1",
  tags: ["research"],
  starter_prompts: ["Search news"],
  tools: [{ native: "web_search", user_toggle: true }],
};
