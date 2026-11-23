import { ArrowLeft, Plus, Pencil, Trash2, X } from "lucide-react";
import { Link } from "react-router-dom";
import type { Agent, Conversation } from "../api/types";
import { groupConversations } from "../lib/date";
import { Avatar } from "./AgentCard";
export default function Sidebar({
  agent,
  conversations,
  current,
  open,
  onClose,
  onNew,
  onRename,
  onDelete,
  busy,
}: {
  agent: Agent;
  conversations: Conversation[];
  current?: string;
  open: boolean;
  onClose: () => void;
  onNew: () => void;
  onRename: (id: string) => void;
  onDelete: (id: string) => void;
  busy: boolean;
}) {
  return (
    <>
      <button
        className={`sidebar-scrim ${open ? "visible" : ""}`}
        aria-label="Close sidebar"
        tabIndex={open ? 0 : -1}
        onClick={onClose}
      />
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="row between">
          <Link to="/" className="back-link">
            <ArrowLeft size={16} />
            All agents
          </Link>
          <button
            className="icon-button mobile"
            aria-label="Close navigation"
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>
        <div className="sidebar-agent">
          <Avatar agent={agent} />
          <div>
            <strong>{agent.display_name}</strong>
            <p className="small muted">Your conversation space</p>
          </div>
        </div>
        <button className="new-chat" onClick={onNew} disabled={busy}>
          <Plus size={17} />
          New chat<kbd>⌘ K</kbd>
        </button>
        <nav aria-label="Conversations">
          {groupConversations(conversations).map(([label, rows]) => (
            <section key={label}>
              <h3>{label}</h3>
              {rows.map((chat) => (
                <div
                  key={chat.id}
                  className={`chat-link ${chat.id === current ? "active" : ""}`}
                >
                  <Link
                    to={`/agents/${agent.name}/c/${chat.id}`}
                    onClick={onClose}
                  >
                    {chat.title}
                  </Link>
                  <details>
                    <summary aria-label={`Actions for ${chat.title}`}>
                      ⋯
                    </summary>
                    <div className="chat-menu">
                      <button disabled={busy} onClick={() => onRename(chat.id)}>
                        <Pencil size={13} />
                        Rename
                      </button>
                      <button disabled={busy} onClick={() => onDelete(chat.id)}>
                        <Trash2 size={13} />
                        Delete
                      </button>
                    </div>
                  </details>
                </div>
              ))}
            </section>
          ))}
        </nav>
        <p className="sidebar-footer">Agent Hub · Personal workspace</p>
      </aside>
    </>
  );
}
