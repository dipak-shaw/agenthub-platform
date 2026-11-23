import { request } from "./client";
import type { Agent, Health } from "./types";
export const getAgents = () => request<Agent[]>("/api/agents");
export const getAgent = (name: string) =>
  request<Agent>(`/api/agents/${encodeURIComponent(name)}`);
export const getHealth = () => request<Health>("/health");
