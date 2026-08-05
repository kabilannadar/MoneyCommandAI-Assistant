import { Suspense, lazy } from "react";
import Chatbot from "./components/Chatbot/Chatbot";

const AgentDashboard = lazy(() => import("./pages/AgentDashboard/AgentDashboard"));
const AdminPanel = lazy(() => import("./pages/AdminPanel/AdminPanel"));

function App() {
  const path = window.location.pathname;

  if (path.startsWith("/admin")) {
    return (
      <Suspense fallback={<div style={{ padding: "2rem", color: "#fff" }}>Loading Admin Panel...</div>}>
        <AdminPanel />
      </Suspense>
    );
  }

  if (path.startsWith("/agent")) {
    return (
      <Suspense fallback={<div style={{ padding: "2rem", color: "#fff" }}>Loading Portal...</div>}>
        <AgentDashboard />
      </Suspense>
    );
  }

  return (
    <div style={{ minHeight: "100vh" }}>
      <Chatbot />
    </div>
  );
}

export default App;