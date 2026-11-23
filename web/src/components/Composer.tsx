import { useEffect, useRef, useState } from "react";
import { ArrowUp, Globe, Square } from "lucide-react";
export default function Composer({
  busy,
  searchToggle,
  enabled,
  onToggle,
  onSend,
  onStop,
  limit = 16000,
}: {
  busy: boolean;
  searchToggle: boolean;
  enabled: boolean;
  onToggle: (value: boolean) => void;
  onSend: (text: string) => void;
  onStop: () => void;
  limit?: number;
}) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 180)}px`;
    }
  }, [text]);
  const send = () => {
    if (!busy && text.trim() && text.length <= limit) {
      onSend(text.trim());
      setText("");
    }
  };
  return (
    <div className="composer-wrap">
      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault();
          send();
        }}
      >
        <textarea
          ref={ref}
          aria-label="Message"
          placeholder="Ask anything…"
          rows={1}
          value={text}
          maxLength={limit}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              !event.shiftKey &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault();
              send();
            }
          }}
        />
        <div className="row between">
          <div>
            {searchToggle && (
              <button
                type="button"
                className={`search-toggle ${enabled ? "selected" : ""}`}
                aria-pressed={enabled}
                onClick={() => onToggle(!enabled)}
              >
                <Globe size={15} />
                Web search
              </button>
            )}
          </div>
          <div className="row">
            <span className="small muted">
              {text.length.toLocaleString()} / {limit.toLocaleString()}
            </span>
            {busy ? (
              <button
                type="button"
                className="send"
                aria-label="Stop response"
                onClick={onStop}
              >
                <Square size={16} />
              </button>
            ) : (
              <button
                className="send"
                aria-label="Send message"
                disabled={!text.trim()}
              >
                <ArrowUp size={19} />
              </button>
            )}
          </div>
        </div>
      </form>
      <p className="composer-note">
        AI can make mistakes. Check important information.
      </p>
    </div>
  );
}
