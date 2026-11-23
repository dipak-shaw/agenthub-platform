import { useState } from "react";
import { Search, ArrowUpRight, Layers3, MessageSquare } from "lucide-react";
import { Link } from "react-router-dom";
import { useAgents, useHealth } from "../hooks/useAgents";
import { useConversations } from "../hooks/useConversations";
import AgentCard from "../components/AgentCard";
import ThemeToggle from "../components/ThemeToggle";
import EmptyState from "../components/EmptyState";
export default function HomePage() {
  const agents = useAgents();
  const health = useHealth();
  const chats = useConversations();
  const [search, setSearch] = useState("");
  const [tag, setTag] = useState("");
  const tags = [...new Set(agents.data?.flatMap((agent) => agent.tags))];
  const filtered = agents.data?.filter(
    (agent) =>
      `${agent.display_name} ${agent.name} ${agent.description} ${agent.tags.join(" ")}`
        .toLowerCase()
        .includes(search.toLowerCase()) &&
      (!tag || agent.tags.includes(tag)),
  );
  return (
    <div className="home">
      <header className="home-header">
        <Link to="/" className="brand">
          <span>
            <Layers3 size={19} />
          </span>
          Agent Hub
        </Link>
        <div className="row">
          <span className="health-badge">
            <i />
            {health.data?.model_mode === "foundry" ? "Foundry" : "Demo mode"}
            <span className="health-detail">
              {" "}
              · {health.data?.search_provider || "offline"}
            </span>
          </span>
          <ThemeToggle />
        </div>
      </header>
      <main className="home-main">
        <div className="eyebrow">A little help. A lot of possibility.</div>
        <h1>What are we exploring today?</h1>
        <p className="home-subtitle">
          A thoughtful answer starts with the right conversation.
        </p>
        <div className="catalog-heading">
          <h2>
            Your agents <span>{agents.data?.length || 0}</span>
          </h2>
          <label className="search-box">
            <Search size={17} />
            <input
              aria-label="Search agents"
              placeholder="Find an agent…"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
        </div>
        {!!tags.length && (
          <div className="filter-tags">
            <button className={!tag ? "active" : ""} onClick={() => setTag("")}>
              All agents
            </button>
            {tags.map((value) => (
              <button
                key={value}
                className={tag === value ? "active" : ""}
                onClick={() => setTag(value)}
              >
                {value}
              </button>
            ))}
          </div>
        )}
        {agents.isPending ? (
          <p role="status">Loading your workspace…</p>
        ) : agents.error ? (
          <div role="alert">
            Unable to load agents.{" "}
            <button onClick={() => agents.refetch()}>Try again</button>
          </div>
        ) : agents.data?.length === 0 ? (
          <EmptyState>
            <p>
              Add an <code>agent_hub/agents/&lt;name&gt;/agent.yaml</code> and
              system prompt, then restart the app.
            </p>
            <p>No agents are bundled. This workspace is yours to create.</p>
          </EmptyState>
        ) : filtered?.length === 0 ? (
          <EmptyState title="No matching agents">
            <p>Try another search or tag.</p>
          </EmptyState>
        ) : (
          <div className="agent-grid">
            {filtered?.map((agent) => (
              <AgentCard key={agent.name} agent={agent} />
            ))}
          </div>
        )}
        {!!chats.data?.length && (
          <section className="recent">
            <h2>Pick up where you left off</h2>
            <div className="recent-grid">
              {chats.data.slice(0, 5).map((chat) => (
                <Link
                  key={chat.id}
                  to={`/agents/${chat.agent_name}/c/${chat.id}`}
                >
                  <MessageSquare size={17} />
                  <span>
                    <strong>{chat.title}</strong>
                    <small>
                      {agents.data?.find(
                        (agent) => agent.name === chat.agent_name,
                      )?.display_name || chat.agent_name}
                    </small>
                  </span>
                  <ArrowUpRight size={15} />
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>
      <footer className="home-footer">
        Made for curiosity. Built around you.
      </footer>
    </div>
  );
}
