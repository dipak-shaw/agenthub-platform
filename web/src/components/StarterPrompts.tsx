export default function StarterPrompts({
  prompts,
  onSelect,
}: {
  prompts: string[];
  onSelect: (prompt: string) => void;
}) {
  return (
    <div className="starter-prompts">
      {prompts.map((prompt) => (
        <button key={prompt} onClick={() => onSelect(prompt)}>
          {prompt}
          <span>↗</span>
        </button>
      ))}
    </div>
  );
}
