import { ArrowUpRight, Globe } from "lucide-react";
import { Link } from "react-router-dom";
import type { Agent } from "../api/types";
export function Avatar({ agent }: { agent: Agent }) {
  return agent.avatar_url ? (
    <img className="avatar" src={agent.avatar_url} alt="" />
  ) : (
    <span className="avatar" aria-hidden="true">
      {agent.avatar}
    </span>
  );
}
export default function AgentCard({ agent }: { agent: Agent }) {
  return (
    <Link
      to={`/agents/${agent.name}`}
      className="agent-card"
      style={{ borderTopColor: agent.accent_color }}
    >
      <div className="row between">
        <Avatar agent={agent} />
        {agent.tools.some((tool) => tool.native === "web_search") && (
          <Globe size={17} aria-label="Web search available" />
        )}
      </div>
      <h3>{agent.display_name}</h3>
      <p className="clamp">{agent.description}</p>
      <div className="tags">
        {agent.tags.map((tag) => (
          <span key={tag}>{tag}</span>
        ))}
      </div>
      <div className="row between card-action">
        <span>Start chat</span>
        <ArrowUpRight size={18} />
      </div>
    </Link>
  );
}
