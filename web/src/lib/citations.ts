import type { Source } from "../api/types";
export function citationMarkdown(text: string, sources: Source[]): string {
  // Preserve code blocks and inline code verbatim.
  return text
    .split(/(```[\s\S]*?```|`[^`]*`)/g)
    .map((part) =>
      part.startsWith("`")
        ? part
        : part.replace(/\[(\d+)\](?!\()/g, (marker, index: string) =>
            sources.some((source) => source.index === Number(index))
              ? `[${index}](#source-${index})`
              : marker,
          ),
    )
    .join("");
}
export function domain(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return "source";
  }
}
