import { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";
import "./AgentDashboard.css";
import { API_BASE, SOCKET_URL } from "../../config";

const EyeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ display: "block" }}>
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const EyeOffIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ display: "block" }}>
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
    <line x1="1" y1="1" x2="23" y2="23" />
  </svg>
);

// ─────────────────────────────────────────────────────── //
// Login Screen                                            //
// ─────────────────────────────────────────────────────── //
function AgentLogin({ onLogin }) {
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);

  const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const isPasswordValid = password.length > 0;

  async function handleSubmit(e) {
    e.preventDefault();
    setEmailTouched(true);
    setPasswordTouched(true);
    if (!isEmailValid || !isPasswordValid) return;

    setError(""); setLoading(true);
    try {
      const res  = await fetch(`${API_BASE}/agent/login`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");
      localStorage.setItem("moneycommandai_agent_token",    data.token);
      localStorage.setItem("moneycommandai_agent_id",       String(data.agent_id));
      localStorage.setItem("moneycommandai_agent_name",     data.name);
      onLogin({ token: data.token, agent_id: data.agent_id, name: data.name });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="agd-login-wrapper">
      <div className="agd-login-card">
        <div className="agd-login-logo" style={{
          background: "linear-gradient(135deg, #1D71B8, #155a99)",
          borderRadius: "50%",
          width: "60px",
          height: "60px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#ffffff",
          marginBottom: "0.5rem",
          boxShadow: "0 4px 12px rgba(29, 113, 184, 0.25)"
        }}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: "block" }}>
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </div>
        <h1 className="agd-login-title">Agent Dashboard</h1>
        <p className="agd-login-sub">MoneyCommandAI Support Team Portal</p>

        {error && <div className="agd-login-error">{error}</div>}

        <form className="agd-login-form" onSubmit={handleSubmit}>
          <div className="agd-input-group">
            <input
              id="agd-email"
              type="email"
              className={`agd-login-input ${emailTouched && !isEmailValid ? "agd-input-error" : ""}`}
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={() => setEmailTouched(true)}
              required
              autoFocus
            />
            {emailTouched && !email && (
              <span className="agd-validation-msg">Email is required.</span>
            )}
            {emailTouched && email && !isEmailValid && (
              <span className="agd-validation-msg">Invalid email format.</span>
            )}
          </div>

          <div className="agd-input-group">
            <div className="agd-password-wrapper" style={{ position: "relative", width: "100%" }}>
              <input
                id="agd-password"
                type={showPassword ? "text" : "password"}
                className={`agd-login-input ${passwordTouched && !isPasswordValid ? "agd-input-error" : ""}`}
                placeholder="Password"
                style={{ paddingRight: "2.75rem" }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onBlur={() => setPasswordTouched(true)}
                required
              />
              <button
                type="button"
                className="agd-password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            </div>
            {passwordTouched && !password && (
              <span className="agd-validation-msg">Password is required.</span>
            )}
          </div>

          <button
            id="agd-login-btn"
            className="agd-login-btn"
            type="submit"
            disabled={loading || !isEmailValid || !isPasswordValid}
          >
            {loading ? <span className="agd-spinner" /> : "Login →"}
          </button>
        </form>
      </div>
    </div>
  );
}


function formatTimestamp(ts) {
  if (!ts) return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  let dateStr = ts;
  if (typeof ts === "string" && !ts.endsWith("Z") && !ts.includes("+")) {
    dateStr = ts + "Z";
  }
  try {
    return new Date(dateStr).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch (e) {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
}


function getResolutionDetails(type) {
  if (type === "resolved") {
    return { text: "✓ Resolved", label: "Resolved", color: "#065f46", bg: "#d1fae5" };
  }
  if (type === "message") {
    return { text: "✉ Msg Sent", label: "Msg Sent", color: "#0891b2", bg: "#ecfeff" };
  }
  if (type === "mail") {
    return { text: "✉ Mail Req", label: "Mail Req", color: "#0369a1", bg: "#e0f2fe" };
  }
  if (type === "phone") {
    return { text: "📞 Phone Req", label: "Phone Req", color: "#4f46e5", bg: "#e0e7ff" };
  }
  if (type === "chatbot") {
    return { text: "🤖 Chatbot", label: "Chatbot", color: "#475569", bg: "#f1f5f9" };
  }
  return { text: "✕ Ended", label: "Ended", color: "#991b1b", bg: "#fee2e2" };
}


// ─────────────────────────────────────────────────────── //
// Main Dashboard                                          //
// ─────────────────────────────────────────────────────── //
function Dashboard({ agent }) {
  const [queue,           setQueue]           = useState([]);
  const [activeSessions,  setActiveSessions]  = useState([]);   // { user_id, user_name, session_id }
  const [pastChats,       setPastChats]       = useState([]);    // Resolved chat sessions
  const [selectedSession, setSelectedSession] = useState(null);  // currently open chat
  const [messages,        setMessages]        = useState({});    // { session_id: [msg, ...] }
  const [input,           setInput]           = useState("");
  const [isTyping,        setIsTyping]        = useState({});    // { session_id: bool }
  const [mobileView,      setMobileView]      = useState("sidebar"); // "sidebar" | "chat"
  const [userStatuses,    setUserStatuses]    = useState({});    // { user_id: "online" | "offline" }
  const [isQueueExpanded, setIsQueueExpanded]   = useState(true);
  const [isActiveExpanded, setIsActiveExpanded] = useState(true);
  const [isPastExpanded, setIsPastExpanded]     = useState(true);
  const [mainTab,         setMainTab]         = useState("dashboard"); // "dashboard" | "all-chats"
  const [currentTime,     setCurrentTime]     = useState(() => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
  const [searchTerm,      setSearchTerm]      = useState("");
  const [statusFilter,    setStatusFilter]    = useState("all"); // "all" | "resolved" | "ended"

  const [showProfileModal, setShowProfileModal] = useState(false);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState("");

  useEffect(() => {
    if (selectedSession) {
      setEditName(selectedSession.raw_name || "");
      setEditEmail(selectedSession.raw_email || "");
      setProfileError("");
    }
  }, [selectedSession]);

  const isNameUserProvided = selectedSession && selectedSession.raw_name && !selectedSession.name_by_agent;
  const isEmailUserProvided = selectedSession && selectedSession.raw_email && !selectedSession.email_by_agent;

  async function handleSaveProfile(e) {
    e.preventDefault();
    if (!selectedSession) return;
    setSavingProfile(true);
    setProfileError("");
    try {
      const res = await fetch(`${API_BASE}/agent/users/${selectedSession.user_id}/profile`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${agent.token}`
        },
        body: JSON.stringify({
          name: isNameUserProvided ? undefined : editName,
          email: isEmailUserProvided ? undefined : editEmail
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update profile");
      
      setSelectedSession((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          user_name: data.name || data.phone || `User ${data.id}`,
          user_email: data.email,
          raw_name: data.raw_name,
          raw_email: data.raw_email,
          name_by_agent: data.name_by_agent,
          email_by_agent: data.email_by_agent
        };
      });
      setActiveSessions((prev) =>
        prev.map((s) =>
          s.user_id === selectedSession.user_id
            ? {
                ...s,
                user_name: data.name || data.phone || `User ${data.id}`,
                user_email: data.email,
                raw_name: data.raw_name,
                raw_email: data.raw_email,
                name_by_agent: data.name_by_agent,
                email_by_agent: data.email_by_agent
              }
            : s
        )
      );
      setShowProfileModal(false);
    } catch (err) {
      setProfileError(err.message);
    } finally {
      setSavingProfile(false);
    }
  }

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const [hiddenChats,     setHiddenChats]       = useState(() => {
    try {
      const stored = localStorage.getItem("moneycommandai_hidden_chats");
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const hideChat = (sessionId) => {
    setHiddenChats((prev) => {
      const next = [...prev, sessionId];
      localStorage.setItem("moneycommandai_hidden_chats", JSON.stringify(next));
      return next;
    });
    setSelectedSession((curr) => {
      if (curr && curr.session_id === sessionId && curr.is_resolved) {
        return null;
      }
      return curr;
    });
  };

  const clearAllPastChats = () => {
    const allIds = pastChats.map((sess) => sess.session_id);
    setHiddenChats((prev) => {
      const next = Array.from(new Set([...prev, ...allIds]));
      localStorage.setItem("moneycommandai_hidden_chats", JSON.stringify(next));
      return next;
    });
    setSelectedSession((curr) => {
      if (curr && curr.is_resolved) {
        return null;
      }
      return curr;
    });
  };

  const socketRef  = useRef(null);
  const bottomRef  = useRef(null);
  const typingTimer = useRef({});

  const activeSessionsRef = useRef([]);
  useEffect(() => {
    activeSessionsRef.current = activeSessions;
  }, [activeSessions]);

  // ---- Socket.IO ----
  useEffect(() => {
    const socket = io(SOCKET_URL, {
      path:       "/socket.io",
      auth:       { token: agent.token },
      transports: ["polling", "websocket"],
    });
    socketRef.current = socket;

    socket.on("connect", () => {
      socket.emit("agent_available", { token: agent.token });
      socket.emit("get_past_chats", { token: agent.token });
    });

    socket.on("connect_error", (err) => {
      console.warn("[Agent Socket Error]", err.message);
      if (err.message && (err.message.includes("Invalid") || err.message.includes("Authentication"))) {
        localStorage.removeItem("moneycommandai_agent_token");
        localStorage.removeItem("moneycommandai_agent_id");
        localStorage.removeItem("moneycommandai_agent_name");
        window.location.reload();
      }
    });

    socket.on("queue_update", ({ queue: q }) => setQueue(q));

    socket.on("past_chats", ({ past_chats: pc }) => {
      setPastChats(pc);
    });

    socket.on("past_chats_updated", () => {
      socket.emit("get_past_chats", { token: agent.token });
    });

    socket.on("user_status", ({ user_id, status }) => {
      setUserStatuses((prev) => ({
        ...prev,
        [user_id]: status
      }));
    });

    socket.on("user_info_updated", (data) => {
      setActiveSessions((prev) =>
        prev.map((s) =>
          s.user_id === data.user_id
            ? { ...s, user_name: data.user_name, user_email: data.user_email, raw_name: data.raw_name, raw_email: data.raw_email, name_by_agent: data.name_by_agent, email_by_agent: data.email_by_agent }
            : s
        )
      );
      setSelectedSession((curr) => {
        if (curr && curr.user_id === data.user_id) {
          return { ...curr, user_name: data.user_name, user_email: data.user_email, raw_name: data.raw_name, raw_email: data.raw_email, name_by_agent: data.name_by_agent, email_by_agent: data.email_by_agent };
        }
        return curr;
      });
      setQueue((prev) =>
        prev.map((q) =>
          q.user_id === data.user_id
            ? { ...q, user_name: data.user_name, user_email: data.user_email, raw_name: data.raw_name, raw_email: data.raw_email, name_by_agent: data.name_by_agent, email_by_agent: data.email_by_agent }
            : q
        )
      );
    });
    socket.on("user_deleted", ({ user_id }) => {
      setActiveSessions((prev) => prev.filter((s) => s.user_id !== user_id));
      setQueue((prev) => prev.filter((q) => q.user_id !== user_id));
      setPastChats((prev) => prev.filter((pc) => pc.user_id !== user_id));
      setSelectedSession((curr) => {
        if (curr && curr.user_id === user_id) {
          return null;
        }
        return curr;
      });
    });

    socket.on("session_started", ({ user_id, user_name, user_phone, user_email, raw_name, raw_email, name_by_agent, email_by_agent, session_id, user_session_number, preview, is_user_online }) => {
      const newSession = { user_id, user_name, user_phone, user_email, raw_name, raw_email, name_by_agent, email_by_agent, session_id, user_session_number };
      setActiveSessions((prev) => {
        if (prev.some((s) => s.session_id === session_id)) return prev;
        return [...prev, newSession];
      });
      setUserStatuses((prev) => ({
        ...prev,
        [user_id]: is_user_online ? "online" : "offline"
      }));
      setMessages((prev) => ({
        ...prev,
        [session_id]: [
          {
            id:      Date.now(),
            sender:  "system",
            content: `Chat started with ${user_name}. Their last message: "${preview || "N/A"}"`,
          },
        ],
      }));
      setSelectedSession(newSession);
      setMobileView("chat");
      // Fetch session message history from server dynamically
      socket.emit("get_chat_history", { token: agent.token, session_id });
    });

    socket.on("message", ({ content, sender, session_id, timestamp }) => {
      setMessages((prev) => ({
        ...prev,
        [session_id]: [
          ...(prev[session_id] || []),
          { id: Date.now() + Math.random(), sender, content, timestamp },
        ],
      }));
      setIsTyping((prev) => ({ ...prev, [session_id]: false }));
    });

    socket.on("chat_history", ({ session_id, messages: history }) => {
      setMessages((prev) => {
        const formatted = history.map((m) => {
          const rawSender = m.sender_role || m.role;
          const sender = (rawSender === "assistant") ? "chatbot" : rawSender;
          return {
            id:        m.id || Date.now() + Math.random(),
            sender,
            content:   m.content,
            timestamp: m.timestamp
          };
        });
        
        const systemMsg = {
          id: "system-connect-" + session_id,
          sender: "system",
          content: `Chat history loaded.`
        };
        
        return {
          ...prev,
          [session_id]: [systemMsg, ...formatted]
        };
      });
    });

    socket.on("typing", ({ sender, session_id }) => {
      if (sender === "user") {
        setIsTyping((prev) => ({ ...prev, [session_id]: true }));
        clearTimeout(typingTimer.current[session_id]);
        typingTimer.current[session_id] = setTimeout(() => {
          setIsTyping((prev) => ({ ...prev, [session_id]: false }));
        }, 4000);
      }
    });

    socket.on("session_ended", ({ session_id, ended_by }) => {
      setMessages((prev) => ({
        ...prev,
        [session_id]: [
          ...(prev[session_id] || []),
          { id: Date.now(), sender: "system", content: `Session ended by ${ended_by}.` },
        ],
      }));
      setActiveSessions((prev) => prev.filter((s) => s.session_id !== Number(session_id)));
      setSelectedSession((curr) => {
        if (curr?.session_id === Number(session_id)) {
          return { ...curr, is_resolved: true };
        }
        return curr;
      });
    });

    // Auto-logout if the socket connection is rejected (expired/invalid token)
    socket.on("connect_error", (err) => {
      console.warn("[AgentSocket] connect_error:", err.message);
      if (err.message && (err.message.includes("token") || err.message.includes("Authentication"))) {
        localStorage.removeItem("moneycommandai_agent_token");
        localStorage.removeItem("moneycommandai_agent_id");
        localStorage.removeItem("moneycommandai_agent_name");
        window.location.reload();
      }
    });

    socket.on("error", ({ message }) => {
      console.warn("[AgentSocket] error:", message);
      if (message && (message.includes("token") || message.includes("expired") || message.includes("Authentication"))) {
        localStorage.removeItem("moneycommandai_agent_token");
        localStorage.removeItem("moneycommandai_agent_id");
        localStorage.removeItem("moneycommandai_agent_name");
        window.location.reload();
      }
    });

    return () => socket.disconnect();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); },
    [messages, selectedSession, isTyping]);

  // ---- Actions ----
  function pickUser(user_id) {
    socketRef.current?.emit("agent_pick_user", { token: agent.token, user_id });
  }

  function sendMessage(e) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || !selectedSession) return;
    socketRef.current?.emit("send_message", {
      token:      agent.token,
      session_id: selectedSession.session_id,
      content:    text,
    });
    setMessages((prev) => ({
      ...prev,
      [selectedSession.session_id]: [
        ...(prev[selectedSession.session_id] || []),
        { id: Date.now(), sender: "agent", content: text, timestamp: new Date().toISOString() },
      ],
    }));
    setInput("");
  }

  function handleTyping() {
    if (selectedSession) {
      socketRef.current?.emit("typing", { token: agent.token, session_id: selectedSession.session_id });
    }
  }

  function resolveSession(action) {
    if (!selectedSession) return;
    socketRef.current?.emit("end_session", {
      token:      agent.token,
      session_id: selectedSession.session_id,
      action:     action,
    });
    setMobileView("sidebar");
    setSelectedSession(null);
    socketRef.current?.emit("get_past_chats", { token: agent.token });
  }

  async function handleLogout() {
    try {
      await fetch(`${API_BASE}/agent/logout?agent_id=${agent.agent_id}`, {
        method: "POST"
      });
    } catch (err) {
      console.error("Failed to notify backend of agent logout:", err);
    }
    localStorage.removeItem("moneycommandai_agent_token");
    localStorage.removeItem("moneycommandai_agent_id");
    localStorage.removeItem("moneycommandai_agent_name");
    window.location.reload();
  }

  const currentMessages = selectedSession ? (messages[selectedSession.session_id] || []) : [];

  // ─────────────────────────────────────────────────────── //
  // Render                                                   //
  // ─────────────────────────────────────────────────────── //
  return (
    <div className={`agd-layout ${mobileView === "chat" ? "show-chat" : "show-sidebar"} ${selectedSession ? "has-selected-session" : ""}`}>
      {/* Sidebar */}
      <aside className="agd-sidebar">
        <div className="agd-sidebar-header">
          <div className="agd-agent-info">
            <div className="agd-agent-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ display: "block" }}>
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
            <div>
              <div className="agd-agent-name">{agent.name}</div>
              <div className="agd-agent-status"><span className="agd-online-dot" /> Online</div>
            </div>
          </div>
          {/* Logout button — always visible in sidebar header */}
          <button
            id="agd-logout-btn"
            className="agd-logout-btn"
            onClick={handleLogout}
            title="Logout"
          >
            ⏻
          </button>
        </div>

        {/* Tab navigation — always visible below agent info */}
        <div className="agd-sidebar-tabs">
          <button
            id="agd-tab-workspace"
            className={`agd-sidebar-tab ${mainTab === "dashboard" ? "active" : ""}`}
            onClick={() => {
              setSelectedSession(null);
              setMainTab("dashboard");
              setMobileView("sidebar");
            }}
          >
            Workspace
          </button>
          <button
            id="agd-tab-chats"
            className={`agd-sidebar-tab ${mainTab === "all-chats" ? "active" : ""}`}
            onClick={() => {
              setSelectedSession(null);
              setMainTab("all-chats");
              setMobileView("chat");
            }}
          >
            Chats
          </button>
        </div>

        <div className="agd-sidebar-content" style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
          {/* Queue */}
          <div 
            className="agd-section-title" 
            onClick={() => setIsQueueExpanded(!isQueueExpanded)}
            style={{ cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", paddingRight: "1rem", userSelect: "none" }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span>{isQueueExpanded ? "▼" : "▶"}</span>
              <span>Waiting Queue</span>
              {queue.length > 0 && <span className="agd-badge">{queue.length}</span>}
            </span>
          </div>
          {isQueueExpanded && (
            <div className="agd-queue-list" style={{ flex: "none", overflow: "visible", transition: "all 0.2s" }}>
              {queue.length === 0 ? (
                <div className="agd-empty-state">No users waiting</div>
              ) : (
                queue.map((user) => (
                  <div key={user.user_id} className="agd-queue-item">
                    <div className="agd-queue-user">{user.user_name || `User ${user.user_id}`}</div>
                    {user.preview && <div className="agd-queue-preview">"{user.preview}"</div>}
                    <button
                      id={`agd-pick-${user.user_id}`}
                      className="agd-pick-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        pickUser(user.user_id);
                      }}
                    >
                      Accept →
                    </button>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Active Chats */}
          <div 
            className="agd-section-title" 
            onClick={() => setIsActiveExpanded(!isActiveExpanded)}
            style={{ cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", paddingRight: "1rem", userSelect: "none" }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span>{isActiveExpanded ? "▼" : "▶"}</span>
              <span>Active Chats</span>
              {activeSessions.length > 0 && <span className="agd-badge agd-badge--green">{activeSessions.length}</span>}
            </span>
          </div>
          {isActiveExpanded && (
            <div className="agd-active-list" style={{ flex: "none", overflow: "visible", transition: "all 0.2s" }}>
              {activeSessions.length === 0 ? (
                <div className="agd-empty-state">No active chats</div>
              ) : (
                activeSessions.map((sess) => (
                  <div
                    key={sess.session_id}
                    id={`agd-session-${sess.session_id}`}
                    className={`agd-active-item ${selectedSession?.session_id === sess.session_id && !selectedSession.is_resolved ? "selected" : ""}`}
                    onClick={() => {
                      setSelectedSession({ ...sess, is_resolved: false });
                      setMobileView("chat");
                      socketRef.current?.emit("get_chat_history", { token: agent.token, session_id: sess.session_id });
                    }}
                  >
                    <div className="agd-active-user" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", gap: "6px" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: "6px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        <span 
                          className={`status-dot ${userStatuses[sess.user_id] === "online" ? "online" : "offline"}`}
                          style={{
                            width: "8px",
                            height: "8px",
                            borderRadius: "50%",
                            backgroundColor: userStatuses[sess.user_id] === "online" ? "#22c55e" : "#94a3b8",
                            display: "inline-block",
                            flexShrink: 0
                          }}
                        />
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {sess.user_name || sess.user_phone || `User ${sess.user_id}`}
                        </span>
                      </span>
                      <span style={{ fontSize: "0.68rem", fontWeight: "600", color: "#475569", background: "#e2e8f0", padding: "1px 5px", borderRadius: "4px", flexShrink: 0 }}>
                        #{sess.user_session_number || sess.session_id}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Resolved/Past Chats */}
          <div 
            className="agd-section-title" 
            onClick={() => setIsPastExpanded(!isPastExpanded)}
            style={{ cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", paddingRight: "1rem", userSelect: "none" }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span>{isPastExpanded ? "▼" : "▶"}</span>
              <span>Resolved Chats</span>
              {pastChats.filter((sess) => !hiddenChats.includes(sess.session_id)).length > 0 && (
                <span className="agd-badge">
                  {pastChats.filter((sess) => !hiddenChats.includes(sess.session_id)).length}
                </span>
              )}
            </span>
            {isPastExpanded && pastChats.filter((sess) => !hiddenChats.includes(sess.session_id)).length > 0 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  clearAllPastChats();
                }}
                style={{
                  background: "#f1f5f9",
                  border: "1px solid #cbd5e1",
                  borderRadius: "4px",
                  fontSize: "0.68rem",
                  padding: "2px 6px",
                  color: "#64748b",
                  cursor: "pointer",
                  fontWeight: "600"
                }}
              >
                Clear All
              </button>
            )}
          </div>
          {isPastExpanded && (
            <div className="agd-active-list" style={{ flex: "none", overflow: "visible", transition: "all 0.2s" }}>
              {pastChats.filter((sess) => !hiddenChats.includes(sess.session_id)).length === 0 ? (
                <div className="agd-empty-state">No resolved chats</div>
              ) : (
                pastChats.filter((sess) => !hiddenChats.includes(sess.session_id)).map((sess) => (
                  <div
                    key={sess.session_id}
                    id={`agd-past-session-${sess.session_id}`}
                    className={`agd-active-item ${selectedSession?.session_id === sess.session_id && selectedSession.is_resolved ? "selected" : ""}`}
                    onClick={() => {
                      setSelectedSession({ ...sess, is_resolved: true });
                      setMobileView("chat");
                      socketRef.current?.emit("get_chat_history", { token: agent.token, session_id: sess.session_id });
                    }}
                    style={{ position: "relative" }}
                  >
                    <div className="agd-active-user" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", gap: "6px", paddingRight: "2rem" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: "6px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        <span 
                          className="status-dot offline"
                          style={{
                            width: "8px",
                            height: "8px",
                            borderRadius: "50%",
                            backgroundColor: "#94a3b8",
                            display: "inline-block",
                            flexShrink: 0
                          }}
                        />
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {sess.user_name || sess.user_phone || `User ${sess.user_id}`}
                        </span>
                      </span>
                      <span style={{ fontSize: "0.68rem", fontWeight: "600", color: "#64748b", background: "#f1f5f9", padding: "1px 5px", borderRadius: "4px", flexShrink: 0 }}>
                        #{sess.user_session_number || sess.session_id}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.68rem", color: "#64748b", marginTop: "2px", display: "flex", justifyContent: "space-between", paddingRight: "2rem" }}>
                      <span style={{ color: getResolutionDetails(sess.resolution_type).color, fontWeight: "600" }}>{getResolutionDetails(sess.resolution_type).text}</span>
                      <span>{sess.resolved_at ? new Date(sess.resolved_at).toLocaleDateString() : ""}</span>
                    </div>

                    <button
                      className="agd-hide-chat-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        hideChat(sess.session_id);
                      }}
                      title="Hide from dashboard"
                      style={{
                        position: "absolute",
                        right: "10px",
                        top: "50%",
                        transform: "translateY(-50%)",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        fontSize: "0.85rem",
                        padding: "4px",
                        color: "#94a3b8",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        borderRadius: "4px",
                        zIndex: 2
                      }}
                      onMouseOver={(e) => e.currentTarget.style.color = "#ef4444"}
                      onMouseOut={(e) => e.currentTarget.style.color = "#94a3b8"}
                    >
                      ✕
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </aside>

      {/* Chat Area */}
      <main className="agd-chat-area" style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
        {/* Main Header Bar */}
        <header className="agd-main-header" style={{
          height: "72px",
          borderBottom: "1px solid #dde6f0",
          background: "#ffffff",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 1.5rem",
          flexShrink: 0,
          boxSizing: "border-box"
        }}>
          {/* Active tab title (right panel header) */}
          <div style={{ fontSize: "0.95rem", fontWeight: "700", color: "#1a2a3a", display: "flex", alignItems: "center" }}>
            <button
              className="agd-back-btn"
              onClick={() => setMobileView("sidebar")}
              title="Back to sidebar"
            >
              ←
            </button>
            <span>{mainTab === "dashboard" ? "Workspace" : "Chats"}</span>
          </div>

          {/* Clock */}
          <div className="agd-header-clock" style={{ fontSize: "0.9rem", fontWeight: "600", color: "#64748b", fontFamily: "monospace" }}>
            {currentTime}
          </div>
        </header>

        {/* Content Wrapper */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0, overflow: "hidden" }}>
          {selectedSession ? (
            <div style={{ display: "flex", flexDirection: "column", flex: 1, overflow: "hidden" }}>
              {/* Chat Header */}
              <div className="agd-chat-header">
                <div style={{ display: "flex", alignItems: "center", flex: 1, minWidth: 0 }}>
                  {selectedSession.is_resolved ? (
                    <button
                      className="agd-history-back-btn"
                      onClick={() => {
                        setSelectedSession(null);
                        setMobileView("sidebar");
                      }}
                      title="Back to Chats"
                    >
                      ←
                    </button>
                  ) : (
                    <button
                      className="agd-back-btn"
                      onClick={() => setMobileView("sidebar")}
                      title="Back to list"
                    >
                      ←
                    </button>
                  )}
                  <div className="agd-chat-header-info" style={{ minWidth: 0, display: "flex", alignItems: "center" }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                        <div className="agd-chat-header-name">{selectedSession.user_name || selectedSession.user_phone || `User ${selectedSession.user_id}`}</div>
                      </div>
                      <div className="agd-chat-header-sub" style={{ textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                        <span>
                          {selectedSession.user_phone && selectedSession.user_email
                            ? `${selectedSession.user_phone} · ${selectedSession.user_email} · Session #${selectedSession.user_session_number || selectedSession.session_id}`
                            : selectedSession.user_email
                            ? `${selectedSession.user_email} · Session #${selectedSession.user_session_number || selectedSession.session_id}`
                            : selectedSession.user_phone
                            ? `${selectedSession.user_phone} · Session #${selectedSession.user_session_number || selectedSession.session_id}`
                            : `Session #${selectedSession.user_session_number || selectedSession.session_id}`}
                        </span>
                      </div>
                      {(selectedSession.name_by_agent || selectedSession.email_by_agent) && (
                        <div style={{ fontSize: "0.5rem", color: "#94a3b8", marginTop: "1px", lineHeight: "1" }}>
                          details added by agent
                        </div>
                      )}
                    </div>

                    {!selectedSession.is_resolved && (
                      <button
                        className="agd-profile-edit-btn"
                        onClick={() => setShowProfileModal(true)}
                        style={{
                          marginLeft: "12px",
                          background: "#f1f5f9",
                          border: "1px solid #cbd5e1",
                          borderRadius: "6px",
                          width: "30px",
                          height: "30px",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          cursor: "pointer",
                          fontSize: "0.85rem",
                          color: "#64748b",
                          transition: "all 0.15s",
                          flexShrink: 0
                        }}
                        title="Edit User Profile"
                      >
                        ✏️
                      </button>
                    )}
                  </div>
                </div>
                {selectedSession.is_resolved ? (
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    <span style={{
                      fontSize: "0.78rem",
                      fontWeight: "600",
                      color: getResolutionDetails(selectedSession.resolution_type).color,
                      background: getResolutionDetails(selectedSession.resolution_type).bg,
                      padding: "0.45rem 1.1rem",
                      borderRadius: "20px"
                    }}>
                      {getResolutionDetails(selectedSession.resolution_type).text}
                    </span>
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button id="agd-resolve-btn" className="agd-resolve-btn" onClick={() => resolveSession("resolved")}>
                      ✓ Mark Resolved
                    </button>
                    <button id="agd-end-btn" className="agd-end-btn" onClick={() => resolveSession("ended")}>
                      ✕ End Chat
                    </button>
                  </div>
                )}
              </div>

              {/* Messages */}
              <div className="agd-messages" style={{ flex: 1, overflowY: "auto" }}>
                {currentMessages.map((msg) => (
                  <div key={msg.id} className={`agd-msg agd-msg--${msg.sender}`}>
                    {msg.sender === "system" ? (
                      <div className="agd-system-msg">{msg.content}</div>
                    ) : (
                      <div className="agd-msg-wrapper">
                        <div className="agd-msg-sender-label" style={{ fontSize: "0.72rem", fontWeight: "600", color: "#64748b", marginBottom: "3px" }}>
                          {msg.sender === "user" && `👤 ${selectedSession.user_name || "User"}`}
                          {msg.sender === "chatbot" && "🤖 MoneyCommandAI Assistant"}
                          {msg.sender === "agent" && `🎧 ${agent.name} (You)`}
                        </div>
                        <div className="agd-bubble">{msg.content}</div>
                        <div className="agd-msg-time">
                          {formatTimestamp(msg.timestamp)}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {isTyping[selectedSession.session_id] && !selectedSession.is_resolved && (
                  <div className="agd-msg agd-msg--user">
                    <div className="agd-bubble agd-typing-bubble">
                      <span /><span /><span />
                    </div>
                    <div className="agd-msg-time" style={{ fontSize: "0.7rem", color: "#9bafc4", marginTop: "2px", marginLeft: "4px" }}>
                      {selectedSession.user_name || selectedSession.user_phone || "User"} is typing…
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              {/* Input */}
              {!selectedSession.is_resolved ? (
                <form className="agd-input-row" onSubmit={sendMessage}>
                  <input
                    id="agd-msg-input"
                    type="text"
                    className="agd-input"
                    placeholder="Type a reply…"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyUp={handleTyping}
                    autoComplete="off"
                  />
                  <button
                    id="agd-send-btn"
                    type="submit"
                    className="agd-send-btn"
                    disabled={!input.trim()}
                  >
                    Send →
                  </button>
                </form>
              ) : (
                <div className="agd-input-row" style={{ backgroundColor: "#f1f5f9", justifyContent: "center", padding: "1rem" }}>
                  <span style={{ fontSize: "0.85rem", color: "#64748b", fontStyle: "italic" }}>
                    This conversation has ended.
                  </span>
                </div>
              )}
            </div>
          ) : mainTab === "all-chats" ? (
            <div style={{ padding: "2rem", overflowY: "auto", flex: 1 }}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: "700", color: "#1e293b", marginBottom: "1rem" }}>
                Chats History
              </h2>

              {/* Filter controls */}
              <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
                <input
                  type="text"
                  placeholder="🔍 Search name, phone or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    borderRadius: "6px",
                    padding: "0.5rem 1rem",
                    fontSize: "0.85rem",
                    color: "#1e293b",
                    outline: "none",
                    minWidth: "260px",
                    flex: "1 1 auto"
                  }}
                />

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    borderRadius: "6px",
                    padding: "0.5rem 1rem",
                    fontSize: "0.85rem",
                    color: "#475569",
                    cursor: "pointer",
                    outline: "none",
                    minWidth: "140px"
                  }}
                >
                  <option value="all">All Statuses</option>
                  <option value="resolved">✓ Resolved</option>
                  <option value="message">✉ Message Sent</option>
                  <option value="mail">✉ Mail Callback</option>
                  <option value="phone">📞 Phone Callback</option>
                  <option value="chatbot">🤖 Chatbot</option>
                  <option value="ended">✕ Ended</option>
                </select>
              </div>

              {pastChats.length === 0 ? (
                <div className="agd-chat-empty" style={{ height: "300px" }}>
                  <div className="agd-chat-empty-icon" style={{ marginBottom: "1rem", display: "flex", justifyContent: "center" }}>
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    </svg>
                  </div>
                  <div className="agd-chat-empty-title">No resolved chats</div>
                  <div className="agd-chat-empty-sub">Once chats are resolved or ended, they will appear here.</div>
                </div>
              ) : pastChats.filter((sess) => {
                const query = searchTerm.toLowerCase().trim();
                const nameMatch = (sess.user_name || "").toLowerCase().includes(query);
                const phoneMatch = (sess.user_phone || "").toLowerCase().includes(query);
                const emailMatch = (sess.user_email || "").toLowerCase().includes(query);
                const searchMatch = !query || nameMatch || phoneMatch || emailMatch;
                const statusMatch = statusFilter === "all" || 
                  (statusFilter === "resolved" && sess.resolution_type === "resolved") ||
                  (statusFilter === "message" && sess.resolution_type === "message") ||
                  (statusFilter === "mail" && sess.resolution_type === "mail") ||
                  (statusFilter === "phone" && sess.resolution_type === "phone") ||
                  (statusFilter === "chatbot" && sess.resolution_type === "chatbot") ||
                  (statusFilter === "ended" && !["resolved", "mail", "phone", "chatbot", "message"].includes(sess.resolution_type));
                return searchMatch && statusMatch;
              }).length === 0 ? (
                <div className="agd-chat-empty" style={{ height: "300px" }}>
                  <div className="agd-chat-empty-icon" style={{ marginBottom: "1rem", display: "flex", justifyContent: "center" }}>
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8"></circle>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                  </div>
                  <div className="agd-chat-empty-title">No matching chats found</div>
                  <div className="agd-chat-empty-sub">Try refining your search terms or status filters.</div>
                </div>
              ) : (
                <div style={{ background: "#ffffff", borderRadius: "8px", border: "1px solid #dde6f0", overflowX: "auto", width: "100%", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
                  <table style={{ minWidth: "900px", width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.88rem" }}>
                    <thead>
                      <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                        <th style={{ padding: "0.75rem 1rem", fontWeight: "600", color: "#475569" }}>User</th>
                        <th style={{ padding: "0.75rem 1rem", fontWeight: "600", color: "#475569" }}>Phone</th>
                        <th style={{ padding: "0.75rem 1rem", fontWeight: "600", color: "#475569" }}>Email</th>
                        <th style={{ padding: "0.75rem 1rem", fontWeight: "600", color: "#475569" }}>Status</th>
                        <th style={{ padding: "0.75rem 1rem", fontWeight: "600", color: "#475569" }}>Resolved Date</th>
                        <th style={{ padding: "0.75rem 1rem", fontWeight: "600", color: "#475569" }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pastChats.filter((sess) => {
                        const query = searchTerm.toLowerCase().trim();
                        const nameMatch = (sess.user_name || "").toLowerCase().includes(query);
                        const phoneMatch = (sess.user_phone || "").toLowerCase().includes(query);
                        const emailMatch = (sess.user_email || "").toLowerCase().includes(query);
                        const searchMatch = !query || nameMatch || phoneMatch || emailMatch;
                        const statusMatch = statusFilter === "all" || 
                          (statusFilter === "resolved" && sess.resolution_type === "resolved") ||
                          (statusFilter === "message" && sess.resolution_type === "message") ||
                          (statusFilter === "mail" && sess.resolution_type === "mail") ||
                          (statusFilter === "phone" && sess.resolution_type === "phone") ||
                          (statusFilter === "chatbot" && sess.resolution_type === "chatbot") ||
                          (statusFilter === "ended" && !["resolved", "mail", "phone", "chatbot", "message"].includes(sess.resolution_type));
                        return searchMatch && statusMatch;
                      }).map((sess) => (
                        <tr key={sess.session_id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                          <td style={{ padding: "0.75rem 1rem", color: "#1e293b" }}>
                            <div style={{ display: "flex", flexDirection: "column" }}>
                              <span style={{ fontWeight: "600" }}>{sess.user_name || `User ${sess.user_id}`}</span>
                              <span style={{ fontSize: "0.72rem", color: "#64748b", fontWeight: "600" }}>Session #{sess.user_session_number || sess.session_id}</span>
                            </div>
                          </td>
                          <td style={{ padding: "0.75rem 1rem", color: "#64748b" }}>
                            {sess.user_phone || "—"}
                          </td>
                          <td style={{ padding: "0.75rem 1rem", color: "#64748b" }}>
                            {sess.user_email || "—"}
                          </td>
                          <td style={{ padding: "0.75rem 1rem" }}>
                            <span style={{
                              fontSize: "0.75rem",
                              fontWeight: "600",
                              color: getResolutionDetails(sess.resolution_type).color,
                              background: getResolutionDetails(sess.resolution_type).bg,
                              padding: "2px 8px",
                              borderRadius: "12px"
                            }}>
                              {getResolutionDetails(sess.resolution_type).label}
                            </span>
                          </td>
                          <td style={{ padding: "0.75rem 1rem", color: "#64748b" }}>
                            {sess.resolved_at ? new Date(sess.resolved_at).toLocaleString() : "—"}
                          </td>
                          <td style={{ padding: "0.75rem 1rem" }}>
                            <button
                              onClick={() => {
                                setSelectedSession({ ...sess, is_resolved: true });
                                setMobileView("chat");
                                socketRef.current?.emit("get_chat_history", { token: agent.token, session_id: sess.session_id });
                              }}
                              style={{
                                background: "#0284c7",
                                border: "none",
                                borderRadius: "4px",
                                padding: "4px 10px",
                                color: "#ffffff",
                                fontSize: "0.75rem",
                                fontWeight: "600",
                                cursor: "pointer",
                                transition: "background 0.2s"
                              }}
                              onMouseOver={(e) => e.currentTarget.style.background = "#0369a1"}
                              onMouseOut={(e) => e.currentTarget.style.background = "#0284c7"}
                            >
                              View History
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div className="agd-chat-empty" style={{ flex: 1 }}>
              <div className="agd-chat-empty-icon" style={{ marginBottom: "1rem", display: "flex", justifyContent: "center" }}>
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <div className="agd-chat-empty-title">Select a chat to begin</div>
              <div className="agd-chat-empty-sub">Accept a user from the queue or pick a session.</div>
            </div>
          )}
        </div>
    {showProfileModal && selectedSession && (
        <div style={{
          position: "fixed",
          inset: 0,
          background: "rgba(15, 23, 42, 0.45)",
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000
        }}>
          <form onSubmit={handleSaveProfile} style={{
            background: "#ffffff",
            border: "1px solid #dde6f0",
            borderRadius: "16px",
            padding: "1.75rem",
            width: "420px",
            maxWidth: "calc(100vw - 2rem)",
            boxShadow: "0 20px 50px rgba(0,0,0,0.15)",
            display: "flex",
            flexDirection: "column",
            gap: "1.1rem",
            boxSizing: "border-box"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: "700", color: "#1e293b", margin: 0 }}>
                Update User Profile
              </h3>
              <button
                type="button"
                onClick={() => setShowProfileModal(false)}
                style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: "1rem", padding: "0.2rem" }}
              >
                ✕
              </button>
            </div>

            {profileError && (
              <div style={{ background: "#fee2e2", border: "1px solid #fca5a5", borderRadius: "6px", padding: "0.6rem 0.8rem", fontSize: "0.82rem", color: "#991b1b" }}>
                {profileError}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
              <label style={{ fontSize: "0.78rem", fontWeight: "600", color: "#475569" }}>
                Phone Number (User Provided)
              </label>
              <input
                type="text"
                disabled
                value={selectedSession.user_phone || "—"}
                style={{
                  width: "100%",
                  padding: "0.6rem 0.8rem",
                  background: "#f1f5f9",
                  border: "1px solid #cbd5e1",
                  borderRadius: "6px",
                  color: "#64748b",
                  fontSize: "0.9rem",
                  boxSizing: "border-box"
                }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label style={{ fontSize: "0.78rem", fontWeight: "600", color: "#475569" }}>
                  User Name
                </label>
                {selectedSession.name_by_agent && (
                  <span style={{ fontSize: "0.68rem", color: "#3b82f6", fontWeight: "600" }}>
                    ✍️ Added by Agent
                  </span>
                )}
              </div>
              <input
                type="text"
                disabled={isNameUserProvided}
                placeholder="Enter user name..."
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.6rem 0.8rem",
                  background: isNameUserProvided ? "#f8fafc" : "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: "6px",
                  color: isNameUserProvided ? "#94a3b8" : "#1e293b",
                  fontSize: "0.9rem",
                  outline: "none",
                  boxSizing: "border-box"
                }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label style={{ fontSize: "0.78rem", fontWeight: "600", color: "#475569" }}>
                  Email Address
                </label>
                {selectedSession.email_by_agent && (
                  <span style={{ fontSize: "0.68rem", color: "#3b82f6", fontWeight: "600" }}>
                    ✍️ Added by Agent
                  </span>
                )}
              </div>
              <input
                type="email"
                disabled={isEmailUserProvided}
                placeholder="Enter email address..."
                value={editEmail}
                onChange={(e) => setEditEmail(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.6rem 0.8rem",
                  background: isEmailUserProvided ? "#f8fafc" : "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: "6px",
                  color: isEmailUserProvided ? "#94a3b8" : "#1e293b",
                  fontSize: "0.9rem",
                  outline: "none",
                  boxSizing: "border-box"
                }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.6rem", marginTop: "0.5rem" }}>
              <button
                type="button"
                onClick={() => setShowProfileModal(false)}
                style={{
                  background: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: "6px",
                  padding: "0.5rem 1rem",
                  fontSize: "0.85rem",
                  fontWeight: "600",
                  color: "#475569",
                  cursor: "pointer"
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={savingProfile || (isNameUserProvided && isEmailUserProvided)}
                style={{
                  background: "#0284c7",
                  border: "none",
                  borderRadius: "6px",
                  padding: "0.5rem 1rem",
                  fontSize: "0.85rem",
                  fontWeight: "600",
                  color: "#ffffff",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.4rem"
                }}
              >
                {savingProfile ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </div>
      )}
      </main>
    </div>
  );
}


// ─────────────────────────────────────────────────────── //
// Root Export                                             //
// ─────────────────────────────────────────────────────── //
export default function AgentDashboard() {
  const [agent, setAgent] = useState(() => {
    const token    = localStorage.getItem("moneycommandai_agent_token");
    const agent_id = localStorage.getItem("moneycommandai_agent_id");
    const name     = localStorage.getItem("moneycommandai_agent_name");
    return token ? { token, agent_id: Number(agent_id), name } : null;
  });

  useEffect(() => {
    if (!agent) return;
    fetch(`${API_BASE}/agent/me`, {
      headers: {
        "Authorization": `Bearer ${agent.token}`
      }
    })
      .then((res) => {
        if (res.status === 401) {
          throw new Error("Session expired");
        }
        if (!res.ok) {
          throw new Error("Failed to fetch profile");
        }
        return res.json();
      })
      .then((data) => {
        if (data.name && data.name !== agent.name) {
          localStorage.setItem("moneycommandai_agent_name", data.name);
          setAgent(prev => prev ? { ...prev, name: data.name } : null);
        }
      })
      .catch((err) => {
        console.error("[PROFILE SYNC ERROR] Failed to sync agent name:", err);
        if (err.message === "Session expired") {
          localStorage.removeItem("moneycommandai_agent_token");
          localStorage.removeItem("moneycommandai_agent_id");
          localStorage.removeItem("moneycommandai_agent_name");
          setAgent(null);
        }
      });
  }, []); // eslint-disable-next-line react-hooks/exhaustive-deps

  if (!agent) return <AgentLogin onLogin={setAgent} />;
  return <Dashboard agent={agent} />;
}
