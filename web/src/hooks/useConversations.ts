import { useQuery } from "@tanstack/react-query";
import { getConversations, getConversation } from "../api/conversations";
export const useConversations = (agent?: string) =>
  useQuery({
    queryKey: ["conversations", agent],
    queryFn: () => getConversations(agent),
  });
export const useConversation = (id?: string) =>
  useQuery({
    queryKey: ["conversation", id],
    queryFn: () => getConversation(id!),
    enabled: !!id,
  });
