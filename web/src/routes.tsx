import { Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ChatPage from "./pages/ChatPage";
import NotFoundPage from "./pages/NotFoundPage";
export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/agents/:name" element={<ChatPage />} />
      <Route path="/agents/:name/c/:conversationId" element={<ChatPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
