import { Globe, LoaderCircle } from "lucide-react";
export default function ToolStatus({
  active,
  searched,
}: {
  active: string | null;
  searched: boolean;
}) {
  return active ? (
    <div className="tool-status" role="status">
      <LoaderCircle size={15} className="spin" />
      {active}
    </div>
  ) : searched ? (
    <div className="tool-status muted">
      <Globe size={14} />
      Searched the web
    </div>
  ) : null;
}
