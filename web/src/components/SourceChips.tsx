import { Globe } from "lucide-react";
import type { Source } from "../api/types";
import { domain } from "../lib/citations";
export default function SourceChips({ sources }: { sources: Source[] }) {
  return sources.length ? (
    <div className="sources" aria-label="Sources">
      {sources.map((source) => (
        <a
          className="source-chip"
          key={source.url}
          href={source.url}
          title={source.snippet}
          target="_blank"
          rel="noopener noreferrer"
        >
          <Globe size={14} />
          <span>
            <small>
              {source.index} · {domain(source.url)}
            </small>
            <strong>{source.title}</strong>
          </span>
        </a>
      ))}
    </div>
  ) : null;
}
