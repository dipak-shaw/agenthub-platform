import { useEffect, useRef, useState } from "react";
import { ArrowDown, Menu } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useAgent, useHealth } from "../hooks/useAgents";
import { useConversation, useConversations } from "../hooks/useConversations";
import { useChatStream } from "../hooks/useChatStream";
import { useAutoScroll } from "../hooks/useAutoScroll";
import { renameConversation, deleteConversation } from "../api/conversations";
import type { Message } from "../api/types";
import Sidebar from "../components/Sidebar";
import { Avatar } from "../components/AgentCard";
import ChatMessage from "../components/ChatMessage";
import Composer from "../components/Composer";
import StarterPrompts from "../components/StarterPrompts";
import ThemeToggle from "../components/ThemeToggle";
import DemoBanner from "../components/DemoBanner";
import NotFoundPage from "./NotFoundPage";

export default function ChatPage() {
  const { name = "", conversationId } = useParams();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const agent = useAgent(name);
  const health = useHealth();
  const conversations = useConversations(name);
  const conversation = useConversation(conversationId);
  const stream = useChatStream();
  const { busy, clear } = stream;
  const [enabled, setEnabled] = useState(true);
  const [sidebar, setSidebar] = useState(false);
  const [optimistic, setOptimistic] = useState<Message[] | null>(null);
  const [notice, setNotice] = useState("");
  const [edit, setEdit] = useState<{
    id: string;
    title: string;
    action: "rename" | "delete";
  } | null>(null);
  const activeId = useRef(conversationId);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (edit) dialog.current?.showModal();
    else dialog.current?.close();
  }, [edit]);
  useEffect(() => {
    if (!busy && activeId.current !== conversationId) {
      setOptimistic(null);
      clear();
      activeId.current = conversationId;
    }
  }, [conversationId, busy, clear]);
  const messages = optimistic ?? conversation.data?.messages ?? [];
  const scroll = useAutoScroll(
    `${stream.reply?.content || ""}:${messages.length}:${stream.tool}`,
  );
  const newChat = () => {
    if (busy) return;
    setOptimistic(null);
    clear();
    activeId.current = undefined;
    navigate(`/agents/${name}`);
    setSidebar(false);
  };
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (!busy) {
          setOptimistic(null);
          clear();
          activeId.current = undefined;
          navigate(`/agents/${name}`);
        }
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [name, navigate, busy, clear]);
  const send = async (text: string, regenerate = false) => {
    if (busy) return;
    setNotice("");
    const base = conversation.data?.messages ?? [];
    setOptimistic(
      regenerate
        ? base.slice(0, -1)
        : [
            ...base,
            {
              id: "new-user",
              role: "user",
              content: text,
              sources: [],
              status: "complete",
            },
          ],
    );
    let cid = conversationId;
    await stream.start(
      name,
      {
        message: text,
        conversation_id: conversationId,
        web_search_enabled: enabled,
        regenerate,
      },
      (id) => {
        cid = id;
        activeId.current = id;
        navigate(`/agents/${name}/c/${id}`, { replace: true });
      },
    );
    await cache.invalidateQueries({ queryKey: ["conversations"] });
    if (cid) {
      await cache.invalidateQueries({ queryKey: ["conversation", cid] });
      setOptimistic(null);
      clear();
    }
  };
  const saveEdit = async () => {
    if (!edit) return;
    try {
      if (edit.action === "rename")
        await renameConversation(edit.id, edit.title);
      else {
        await deleteConversation(edit.id);
        if (edit.id === conversationId) newChat();
      }
      await cache.invalidateQueries({ queryKey: ["conversations"] });
      setEdit(null);
    } catch (error) {
      setNotice(
        error instanceof Error ? error.message : "Unable to update chat",
      );
    }
  };
  if (agent.isPending)
    return (
      <p className="loading" role="status">
        Opening your conversation…
      </p>
    );
  if (!agent.data) return <NotFoundPage />;
  const data = agent.data;
  return (
    <div className="chat-layout">
      <Sidebar
        agent={data}
        conversations={conversations.data || []}
        current={conversationId}
        open={sidebar}
        onClose={() => setSidebar(false)}
        onNew={newChat}
        busy={busy}
        onRename={(id) =>
          setEdit({
            id,
            title:
              conversations.data?.find((chat) => chat.id === id)?.title || "",
            action: "rename",
          })
        }
        onDelete={(id) => setEdit({ id, title: "", action: "delete" })}
      />
      <main className="chat-main">
        <header className="chat-header">
          <div className="row">
            <button
              className="icon-button mobile"
              aria-label="Open navigation"
              onClick={() => setSidebar(true)}
            >
              <Menu size={19} />
            </button>
            <span
              className="accent-dot"
              style={{ background: data.accent_color }}
            />
            <strong>{data.display_name}</strong>
            <span className="small muted">
              {conversation.data?.title || "New conversation"}
            </span>
          </div>
          <ThemeToggle />
        </header>
        {health.data?.model_mode === "demo" && <DemoBanner />}
        <div
          className="messages-scroll"
          ref={scroll.ref}
          onScroll={scroll.onScroll}
        >
          <div className="message-column">
            {!messages.length && !stream.reply && (
              <div className="chat-welcome">
                <Avatar agent={data} />
                <h1>Meet {data.display_name}</h1>
                <p>{data.description}</p>
                <StarterPrompts
                  prompts={data.starter_prompts}
                  onSelect={(text) => void send(text)}
                />
              </div>
            )}
            {messages.map((message, index) => (
              <ChatMessage
                key={message.id}
                message={message}
                agent={data}
                onRegenerate={
                  !busy &&
                  index === messages.length - 1 &&
                  message.role === "assistant"
                    ? () =>
                        void send(
                          messages[index - 1]?.content || "Regenerate",
                          true,
                        )
                    : undefined
                }
              />
            ))}
            {stream.reply && (
              <ChatMessage
                message={stream.reply}
                agent={data}
                streaming={busy}
                tool={stream.tool}
              />
            )}
            {(stream.error || notice || conversation.error) && (
              <p className="error-notice" role="alert">
                {stream.error || notice || conversation.error?.message}
              </p>
            )}
          </div>
        </div>
        {scroll.away && (
          <button className="jump" onClick={scroll.jump}>
            <ArrowDown size={15} />
            Jump to latest
          </button>
        )}
        <Composer
          busy={busy}
          enabled={enabled}
          onToggle={setEnabled}
          searchToggle={data.tools.some(
            (tool) => tool.native === "web_search" && tool.user_toggle,
          )}
          onSend={(text) => void send(text)}
          onStop={() => void stream.stop()}
          limit={health.data?.max_message_chars}
        />
      </main>
      <dialog
        ref={dialog}
        className="edit-dialog"
        onCancel={() => setEdit(null)}
      >
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void saveEdit();
          }}
        >
          <h2>
            {edit?.action === "rename"
              ? "Rename conversation"
              : "Delete conversation?"}
          </h2>
          {edit?.action === "rename" ? (
            <input
              aria-label="Conversation title"
              maxLength={60}
              value={edit.title}
              onChange={(event) =>
                setEdit({ ...edit, title: event.target.value })
              }
              autoFocus
            />
          ) : (
            <p>This removes the conversation and its messages.</p>
          )}
          <div className="row">
            <button type="button" onClick={() => setEdit(null)}>
              Cancel
            </button>
            <button
              className="primary"
              disabled={edit?.action === "rename" && !edit.title.trim()}
            >
              {edit?.action === "rename" ? "Save" : "Delete"}
            </button>
          </div>
        </form>
      </dialog>
    </div>
  );
}
