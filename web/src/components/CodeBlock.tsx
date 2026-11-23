import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { copyText } from "../lib/utils";
function textOf(node: React.ReactNode): string {
  if (typeof node === "string") return node;
  if (Array.isArray(node)) return node.map(textOf).join("");
  if (node && typeof node === "object" && "props" in node)
    return textOf((node.props as { children?: React.ReactNode }).children);
  return "";
}
export default function CodeBlock({
  children,
}: {
  children?: React.ReactNode;
}) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="code-block">
      <button
        aria-label="Copy code"
        onClick={async () => {
          setCopied(await copyText(textOf(children)));
          setTimeout(() => setCopied(false), 2000);
        }}
      >
        {copied ? <Check size={14} /> : <Copy size={14} />}{" "}
        {copied ? "Copied" : "Copy code"}
      </button>
      <pre>{children}</pre>
    </div>
  );
}
