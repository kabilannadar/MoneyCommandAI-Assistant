import { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";
import "./LiveChatPanel.css";
import { SOCKET_URL, API_BASE, PERSIST_SESSION } from "../../config";

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
  </svg>
);

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

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


export default function LiveChatPanel({ token, userId, userName, lastPreview, onClose, onMinimize }) {
  const [phase, setPhase]         = useState("connecting"); // connecting | queue | chat | ended
  const [queuePos, setQueuePos]   = useState(null);
  const [queueTotal, setQueueTotal] = useState(null);
  const [agent, setAgent]         = useState(null);         // { name, avatar_url }
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState("");
  const [isTyping, setIsTyping]   = useState(false);        // agent is typing
  const socketRef   = useRef(null);
  const bottomRef   = useRef(null);
  const typingTimer = useRef(null);
  const agentNameRef  = useRef("");
  const sessionIdRef  = useRef(null);   // always up-to-date session id for callbacks

  const phaseRef = useRef(phase);
  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  const [showOptions, setShowOptions] = useState(false);
  const [selectionMessage, setSelectionMessage] = useState("");
  const [hasEmail, setHasEmail] = useState(() => !!localStorage.getItem("moneycommandai_user_email"));
  const [finalNote, setFinalNote] = useState("");
  const [noteStatus, setNoteStatus] = useState("");
  const [waitTimerTrigger, setWaitTimerTrigger] = useState(0);

  // Wait options timer (15 seconds initially, 30 seconds subsequently, can be reset)
  useEffect(() => {
    let timer;
    if (phase === "connecting" || phase === "queue") {
      timer = setTimeout(() => {
        setShowOptions(true);
      }, waitTimerTrigger === 0 ? 15000 : 30000);
    } else {
      const resetTimer = setTimeout(() => {
        setShowOptions(false);
        setSelectionMessage("");
        setWaitTimerTrigger(0);
      }, 0);
      return () => clearTimeout(resetTimer);
    }
    return () => clearTimeout(timer);
  }, [phase, waitTimerTrigger]);

  // ------------------------------------------------------------------ //
  // Socket.IO setup                                                      //
  // ------------------------------------------------------------------ //
  useEffect(() => {
    if (!token) {
      console.warn("[LiveChatPanel] No auth token available yet, waiting...");
      return;
    }
    const socket = io(SOCKET_URL, {
      path:    "/socket.io",
      auth:    { token },
      transports: ["websocket", "polling"],   // websocket first = instant disconnect detection
    });
    socketRef.current = socket;

    socket.on("connect", () => {
      // Join the waiting queue immediately
      socket.emit("user_join_queue", { token, preview: lastPreview || "" });
      setPhase("queue");
    });

    socket.on("queue_position", ({ position, total, session_id }) => {
      setQueuePos(position);
      setQueueTotal(total);
      if (session_id) {
        setSessionId(session_id);
        sessionIdRef.current = session_id;
      }
    });

    socket.on("user_info", (data) => {
      console.log("[Socket] Received user_info:", data);
      if (data) {
        if (data.email) {
          localStorage.setItem("moneycommandai_user_email", data.email);
          setHasEmail(true);
        }
        if (data.phone) {
          localStorage.setItem("moneycommandai_user_phone", data.phone);
        }
        if (data.name) {
          localStorage.setItem("moneycommandai_user_name", data.name);
        }
      }
    });

    socket.on("agent_joined", ({ agent_name, avatar_url, session_id }) => {
      agentNameRef.current  = agent_name;
      sessionIdRef.current  = session_id;    // keep ref in sync
      setAgent({ name: agent_name, avatar_url });
      setSessionId(session_id);
      setPhase("chat");
      // Fetch session message history from server dynamically
      socket.emit("get_chat_history", { token, session_id });
    });

    socket.on("chat_history", ({ session_id, messages: history }) => {
      // JSON storage uses "role" field; legacy Message rows used "sender_role"
      const formatted = history.map((m) => ({
        id:        m.id || Date.now() + Math.random(),
        sender:    m.sender_role || m.role,
        content:   m.content,
        timestamp: m.timestamp
      }));
      
      const systemMsg = {
        id: "system-connect-" + session_id,
        sender: "system",
        content: `Connected with ${agentNameRef.current || "Support Agent"}.`
      };
      
      setMessages([systemMsg, ...formatted]);
    });

    socket.on("message", ({ content, sender, timestamp }) => {
      setMessages((prev) => [...prev, { id: Date.now() + Math.random(), sender, content, timestamp }]);
      setIsTyping(false);
    });

    socket.on("typing", ({ sender }) => {
      if (sender === "agent") {
        setIsTyping(true);
        clearTimeout(typingTimer.current);
        typingTimer.current = setTimeout(() => setIsTyping(false), 4000);
      }
    });

    socket.on("session_ended", ({ ended_by }) => {
      const who = ended_by === "agent" ? agent?.name || "The agent" : "You";
      setMessages((prev) => [...prev, {
        id:      Date.now(),
        sender:  "system",
        content: `${who} ended the chat. Thank you for contacting MoneyCommandAI support!`,
      }]);
      setPhase("ended");
    });

    socket.on("error", ({ message }) => {
      console.warn("[Socket Error]", message);
      if (message && (message.includes("token") || message.includes("Authentication") || message.includes("expired"))) {
        localStorage.removeItem("moneycommandai_user_token");
        localStorage.removeItem("moneycommandai_user_id");
        localStorage.removeItem("moneycommandai_user_name");
        localStorage.removeItem("moneycommandai_user_email");
        localStorage.removeItem("moneycommandai_user_avatar");
        alert("Your session has expired. Please refresh and log in again.");
        window.location.reload();
      }
    });

    socket.on("connect_error", (err) => {
      console.warn("[Socket Connection Error]", err.message);
      socket.disconnect(); // Stop background reconnect attempts while alert is shown
      // Clean up all stale user fields from local storage
      localStorage.removeItem("moneycommandai_user_token");
      localStorage.removeItem("moneycommandai_user_id");
      localStorage.removeItem("moneycommandai_user_name");
      localStorage.removeItem("moneycommandai_user_email");
      localStorage.removeItem("moneycommandai_user_avatar");
      alert("Session expired or authentication failed. Please log in again.");
      window.location.reload();
    });

    // ------------------------------------------------------------------ //
    // Page unload: use sendBeacon — socket.emit is NOT reliable on unload  //
    // sendBeacon() is guaranteed to complete even after the page closes     //
    // ------------------------------------------------------------------ //
    const handleBeforeUnload = () => {
      const currentPhase = phaseRef.current;
      if (currentPhase === "queue" || currentPhase === "connecting") {
        // Fire a guaranteed HTTP request to cancel the waiting session
        const url = `${API_BASE}/api/live/cancel-queue`;
        const payload = JSON.stringify({ token });
        navigator.sendBeacon(url, new Blob([payload], { type: "application/json" }));
      }
      // Active chat: backend disconnect handler takes care of it based on persist_session
    };
    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      const currentPhase = phaseRef.current;
      // On unmount within-app (navigating away from live panel without page refresh)
      if (currentPhase === "queue" || currentPhase === "connecting") {
        socket?.emit("cancel_queue", { token });
      } else if (currentPhase === "chat" && sessionIdRef.current) {
        socket?.emit("end_session", { token, session_id: sessionIdRef.current, action: "user_exited" });
      }
      clearTimeout(typingTimer.current);
      socket?.disconnect();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // ------------------------------------------------------------------ //
  // Send message                                                         //
  // ------------------------------------------------------------------ //
  function sendMessage(e) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || !sessionId || phase !== "chat") return;

    socketRef.current?.emit("send_message", { token, session_id: sessionId, content: text });
    setMessages((prev) => [...prev, { id: Date.now(), sender: "user", content: text }]);
    setInput("");
  }

  function handleTyping() {
    if (sessionId) socketRef.current?.emit("typing", { token, session_id: sessionId });
  }

  function handleEndSession() {
    // Use ref so this always works even if sessionId state is in stale closure
    const sid = sessionIdRef.current;
    if (sid) {
      socketRef.current?.emit("end_session", { token, session_id: sid });
    }
    setPhase("ended");
    onClose();
  }

  function handleSelectOption(optionType) {
    const sid = sessionIdRef.current;
    const noteContent = finalNote.trim() || undefined;

    if (optionType === "chatbot") {
      if (sid) {
        socketRef.current?.emit("end_session", { token, session_id: sid, action: "chatbot", note: noteContent });
      }
      onClose();
    } else if (optionType === "mail") {
      if (sid) {
        socketRef.current?.emit("end_session", { token, session_id: sid, action: "mail", note: noteContent });
      }
      setSelectionMessage("✉ Request for email callback registered. Returning to assistant...");
      setTimeout(() => {
        onClose();
      }, 3000);
    } else if (optionType === "phone") {
      if (sid) {
        socketRef.current?.emit("end_session", { token, session_id: sid, action: "phone", note: noteContent });
      }
      setSelectionMessage("📞 Request for phone call registered. Returning to assistant...");
      setTimeout(() => {
        onClose();
      }, 3000);
    } else if (optionType === "longer") {
      setShowOptions(false);
      setWaitTimerTrigger((prev) => prev + 1);
    }
  }

  function handleSendNote() {
    const text = finalNote.trim();
    if (!text || !sessionId) return;
    socketRef.current?.emit("end_session", { token, session_id: sessionId, action: "message", note: text });
    setFinalNote("");
    setSelectionMessage("✉ Message registered. Returning to assistant...");
    setTimeout(() => {
      onClose();
    }, 3000);
  }

  // ------------------------------------------------------------------ //
  // Render                                                               //
  // ------------------------------------------------------------------ //
  return (
    <div className="lcp-panel">
      {/* Header */}
      <div className="moneycommandai-chat-header">
        <div className="moneycommandai-chat-header__border-line"></div>
        <div className="moneycommandai-chat-header__brand">
          <div className="moneycommandai-chat-header__logo">
            {agent?.avatar_url ? (
              <img
                src={agent.avatar_url}
                alt={agent.name}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  display: "block"
                }}
              />
            ) : (
              <img
                src="/chatbot_mascot.png"
                alt="MoneyCommandAI Support Logo"
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  display: "block"
                }}
              />
            )}
          </div>
          <div className="moneycommandai-chat-header__info">
            <span className="moneycommandai-chat-header__title">
              {phase === "connecting" && "Connecting…"}
              {phase === "queue"      && "Finding an Agent"}
              {phase === "chat"       && (agent?.name || "Support Agent")}
              {phase === "ended"      && "Chat Ended"}
            </span>
            <span className="moneycommandai-chat-header__subtitle">
              {phase === "chat" && <span className="moneycommandai-chat-header__status-dot"></span>}
              <span>
                {phase === "connecting" && "Please wait…"}
                {phase === "queue"      && "Please Wait..."}
                {phase === "chat"       && "Online"}
                {phase === "ended"      && "Session resolved"}
              </span>
            </span>
          </div>
        </div>
        <div className="moneycommandai-chat-header__controls">
          {phase === "chat" && (
            <button
              className="lcp-header-end-btn"
              onClick={handleEndSession}
              title="End Chat Session"
            >
              End Chat
            </button>
          )}
          {phase === "ended" && (
            <button
              className="lcp-header-end-btn"
              onClick={onClose}
              title="Return to Assistant"
            >
              Close
            </button>
          )}
          <button
            className="moneycommandai-chat-header__close"
            onClick={onMinimize}
            aria-label="Minimize chat"
            title="Minimize"
          >
            <CloseIcon />
          </button>
        </div>
      </div>

      {/* Body / Scrollable Area */}
      <div className="moneycommandai-chat-messages" style={{ flex: 1, overflowY: "auto" }}>
        {/* Connecting / Queue Phase Loader Screen */}
        {(phase === "connecting" || phase === "queue") && (
          <div className="lcp-queue-container">
            <div className="lcp-queue-card">
              <div className="lcp-queue-pulse">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <h3 className="lcp-queue-title">
                {phase === "connecting" ? "Connecting to Support..." : "Waiting for Support Agent..."}
              </h3>

              {selectionMessage ? (
                <div className="lcp-wait-message">
                  {selectionMessage}
                </div>
              ) : showOptions ? (
                <>
                  <p className="lcp-queue-text" style={{ fontWeight: "600", color: "var(--moneycommandai-blue-dark)", marginBottom: "4px" }}>
                    Taking longer than expected?
                  </p>
                  <p className="lcp-queue-text">
                    All support agents are currently busy. You can choose to:
                  </p>

                  <div className="lcp-textarea-container" style={{ position: "relative" }}>
                    <textarea
                      className="lcp-textarea-field"
                      placeholder="Message for support agent (optional)..."
                      value={finalNote}
                      onChange={(e) => setFinalNote(e.target.value)}
                      style={{ paddingRight: "35px" }}
                    />
                    <button
                      type="button"
                      className={`lcp-textarea-submit-btn ${finalNote.trim() ? "lcp-textarea-submit-btn--active" : ""}`}
                      onClick={handleSendNote}
                      disabled={!finalNote.trim()}
                      title="Send message to agent"
                    >
                      <SendIcon />
                    </button>
                  </div>
                  {noteStatus && (
                    <div className="lcp-note-status">
                      {noteStatus}
                    </div>
                  )}

                  <div className="lcp-wait-options">
                    <button className="lcp-wait-btn lcp-wait-btn--primary" onClick={() => handleSelectOption("longer")}>
                      ⏳ Keep Waiting
                    </button>
                    <button className="lcp-wait-btn" onClick={() => handleSelectOption("chatbot")}>
                      💬 Continue with Chatbot
                    </button>
                    {hasEmail && (
                      <button className="lcp-wait-btn" onClick={() => handleSelectOption("mail")}>
                        ✉ Wait for Email Callback
                      </button>
                    )}
                    <button className="lcp-wait-btn" onClick={() => handleSelectOption("phone")}>
                      📞 Wait for Phone Call
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p className="lcp-queue-text">
                    An MoneyCommandAI team member will join shortly. Thank you for your patience!
                  </p>
                  <button className="lcp-queue-cancel" onClick={handleEndSession}>
                    Cancel & Go Back
                  </button>
                </>
              )}
            </div>
          </div>
        )}

        {/* Chat / Ended Phase messages */}
        {(phase === "chat" || phase === "ended") && (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                style={{ display: "flex", flexDirection: "column", width: "100%" }}
              >
                {msg.sender === "system" ? (
                  <div className="lcp-system-msg-container">
                    <span className="lcp-system-msg">{msg.content}</span>
                  </div>
                ) : (
                  <>
                    <div className={`moneycommandai-chat-msg moneycommandai-chat-msg--${msg.sender === "user" ? "user" : "bot"}`}>
                      {msg.sender === "agent" && (
                        <div className="moneycommandai-chat-msg__avatar">
                          {agent?.avatar_url ? (
                            <img
                              src={agent.avatar_url}
                              alt={agent.name}
                              style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover" }}
                            />
                          ) : (
                            <img
                              src="/chatbot_mascot.png"
                              alt="MoneyCommandAI Support Logo"
                              style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover" }}
                            />
                          )}
                        </div>
                      )}
                      <div className="moneycommandai-chat-msg__bubble">
                        {msg.content}
                      </div>
                    </div>
                    <div className={`moneycommandai-chat-msg-time-container moneycommandai-chat-msg-time-container--${msg.sender === "user" ? "user" : "bot"}`}>
                      {formatTimestamp(msg.timestamp)}
                    </div>
                  </>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="moneycommandai-chat-msg moneycommandai-chat-msg--bot">
                <div className="moneycommandai-chat-msg__avatar">
                  {agent?.avatar_url ? (
                    <img
                      src={agent.avatar_url}
                      alt={agent.name}
                      style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover" }}
                    />
                  ) : (
                    <img
                      src="/chatbot_mascot.png"
                      alt="MoneyCommandAI Support Logo"
                      style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover" }}
                    />
                  )}
                </div>
                <div className="moneycommandai-chat-typing">
                  <span></span>
                  <span></span>
                  <span></span>
                  <small>{agent?.name || "Agent"} is typing...</small>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Footer / Input Area */}
      {phase === "chat" && (
        <form className="moneycommandai-chat-input-area" onSubmit={sendMessage}>
          <input
            id="lcp-input"
            className="moneycommandai-chat-input"
            type="text"
            placeholder="Type a message…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyUp={handleTyping}
            autoComplete="off"
          />
          <button
            id="lcp-send-btn"
            className={`moneycommandai-chat-send ${input.trim() ? "moneycommandai-chat-send--active" : ""}`}
            type="submit"
            disabled={!input.trim()}
            onClick={sendMessage}
            title="Send"
          >
            <SendIcon />
          </button>
        </form>
      )}

      {phase === "ended" && (
        <div className="lcp-ended-footer">
          <button className="lcp-done-btn" onClick={onClose}>
            Return to Assistant
          </button>
        </div>
      )}
    </div>
  );
}
