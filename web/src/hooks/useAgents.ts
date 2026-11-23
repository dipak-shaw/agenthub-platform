import { useQuery } from "@tanstack/react-query";
import { getAgents, getAgent, getHealth } from "../api/agents";
export const useAgents = () =>
  useQuery({ queryKey: ["agents"], queryFn: getAgents });
export const useAgent = (name: string) =>
  useQuery({ queryKey: ["agent", name], queryFn: () => getAgent(name) });
export const useHealth = () =>
  useQuery({ queryKey: ["health"], queryFn: getHealth, staleTime: 30000 });
