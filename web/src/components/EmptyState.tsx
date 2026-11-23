import { MessageSquare } from "lucide-react";
export default function EmptyState({
  title = "A home for your agents",
  children,
}: {
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="empty-state">
      <MessageSquare size={32} />
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  );
}
