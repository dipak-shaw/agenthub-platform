import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import type { Source } from "../api/types";
import { citationMarkdown } from "../lib/citations";
import CodeBlock from "./CodeBlock";
export default function Markdown({
  text,
  sources,
}: {
  text: string;
  sources: Source[];
}) {
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,
          a: ({ href, children }) => {
            const index = href?.match(/^#source-(\d+)$/)?.[1];
            const source = index
              ? sources.find((item) => item.index === Number(index))
              : undefined;
            return (
              <a
                href={source?.url || href}
                className={source ? "citation" : undefined}
                title={source?.title}
                target="_blank"
                rel="noopener noreferrer"
              >
                {children}
              </a>
            );
          },
        }}
      >
        {citationMarkdown(text, sources)}
      </ReactMarkdown>
    </div>
  );
}
