import { Sparkles } from "lucide-react";
export default function DemoBanner() {
  return (
    <div className="demo-banner">
      <Sparkles size={14} />
      <span>Demo mode · Offline answers and fictional search sources</span>
    </div>
  );
}
