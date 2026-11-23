import { Link } from "react-router-dom";
import EmptyState from "../components/EmptyState";
export default function NotFoundPage() {
  return (
    <main className="home-main">
      <EmptyState title="This page isn't here">
        <Link to="/">Return to your agents</Link>
      </EmptyState>
    </main>
  );
}
