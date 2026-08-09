import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./Chatbot.css";
import UserInfoModal from "../UserInfoModal/UserInfoModal";
import LiveChatPanel from "../LiveChatPanel/LiveChatPanel";
import { API_BASE, PERSIST_SESSION } from "../../config";

function getSuggestions(text) {

  const lower = text.toLowerCase();

  if (lower.includes("telegram") || lower.includes("bot")) {
    return [
      "How to link Bot",
      "Telegram bot setup",
      "Logging commands"
    ];
  }

  if (lower.includes("budget")) {
    return [
      "Set category budget",
      "Monthly budget limit",
      "Recurring budgets"
    ];
  }

  if (lower.includes("feature") || lower.includes("dashboard")) {
    return [
      "Goals & Targets",
      "Spreadsheet export",
      "Receipt attachments"
    ];
  }

  return [
    "Telegram Bot Setup",
    "App Features",
    "Support & Feedback"
  ];
}




/* FAB chat trigger */
const ChatIcon = () => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Filled speech bubble */}
    <path
      d="M20 2H4C2.9 2 2 2.9 2 4v13c0 1.1.9 2 2 2h3l3 3 3-3h7c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"
      fill="#ffffff"
    />
    {/* Three dots */}
    <circle cx="8" cy="10.5" r="1.2" fill="#0b1a30" />
    <circle cx="12" cy="10.5" r="1.2" fill="#0b1a30" />
    <circle cx="16" cy="10.5" r="1.2" fill="#0b1a30" />
  </svg>
);


const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
  </svg>
);

const RefreshIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <polyline points="23 4 23 10 17 10" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

function ensureClickableLinks(text) {
  if (!text) return text;
  let formatted = text;
  
  // 1. Convert plain email addresses (if not already inside [text](mailto:email))
  formatted = formatted.replace(
    /(\[[^\]]+\]\([^)]+\))|((?:mailto:)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}))/g,
    (match, p1, p2, email) => {
      if (p1) return p1;
      return `[${email}](mailto:${email})`;
    }
  );

  // 2. Convert @handle (if not already inside [text](t.me/handle)) and ensure it's not part of an email address
  formatted = formatted.replace(
    /(\[[^\]]+\]\([^)]+\))|((?:https:\/\/t\.me\/)?(?<![a-zA-Z0-9._%+-])@([a-zA-Z0-9_]{5,}))/g,
    (match, p1, p2, handle) => {
      if (p1) return p1;
      return `[@${handle}](https://t.me/${handle})`;
    }
  );

  // 3. Convert plain URLs (if not already inside markdown links)
  formatted = formatted.replace(
    /(\[[^\]]+\]\([^)]+\))|(https?:\/\/[^\s\)]+)/g,
    (match, p1, url) => {
      if (p1) return p1;
      return `[${url}](${url})`;
    }
  );
  
  return formatted;
}


function BotMessage({ text }) {
  const formattedText = ensureClickableLinks(text);
  return (
    <div className="moneycommandai-msg-body">
      <ReactMarkdown>
        {formattedText}
      </ReactMarkdown>
    </div>
  );
}

const BOT_AVATAR = (
  <img
    src="/chatbot_mascot.png"
    alt="MoneyCommandAI Assistant"
    style={{
      width: "30px",
      height: "30px",
      borderRadius: "50%",
      display: "block",
      boxShadow: "0 2.5px 7px rgba(0, 0, 0, 0.08)"
    }}
  />
);

const MoneyCommandAILogo = () => (
  <svg width="22" height="22" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <clipPath id="logoCircle">
      <circle cx="24" cy="24" r="24" />
    </clipPath>
    <image href="/chatbot_mascot.png" width="48" height="48" clipPath="url(#logoCircle)" />
  </svg>
);



const isLoggingPattern = (text) => {
  const lower = text.trim().toLowerCase();
  // Starts with logging command keyword
  if (/^(income|inc|emi|debt|loan|goal|sub|subscription|remind|reminder|cat|category|budget|recurring|recur|repeat)\b/.test(lower)) {
    return true;
  }
  // Or contains numbers (likely an expense command like "coffee 80 cash")
  if (/\d+/.test(lower)) {
    return true;
  }
  return false;
};

export default function Chatbot() {
  const [open, setOpen] = useState(false);
  // true when the closed-state FAB (full size + tooltip) is ready to show.
  // Stays false during the close animation so the FAB/tooltip don't appear
  // before the chat window has finished animating out.
  const [closedFabReady, setClosedFabReady] = useState(true);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [showTooltip, setShowTooltip] = useState(true);
  const [config, setConfig] = useState({ enable_rag: true, enable_live_support: true });

  const fetchConfig = () => {
    fetch(`${API_BASE}/api/config`)
      .then((res) => res.json())
      .then((data) => {
        if (data && typeof data.enable_live_support !== "undefined") {
          setConfig(data);
          if (data.persist_session === false) {
            localStorage.removeItem("moneycommandai_user_token");
            localStorage.removeItem("moneycommandai_user_id");
            localStorage.removeItem("moneycommandai_user_name");
            localStorage.removeItem("moneycommandai_user_email");
            localStorage.removeItem("moneycommandai_user_avatar");
            localStorage.removeItem("moneycommandai_user_phone");
            setAuthUser(null);
          }
        }
      })
      .catch((err) => console.error("Failed to load backend config:", err));
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  // --- Live support state ---
  const [sessionId, setSessionId] = useState(() => {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  });
  const [authUser, setAuthUser] = useState(() => {
    if (!PERSIST_SESSION) {
      localStorage.removeItem("moneycommandai_user_token");
      localStorage.removeItem("moneycommandai_user_id");
      localStorage.removeItem("moneycommandai_user_name");
      localStorage.removeItem("moneycommandai_user_email");
      localStorage.removeItem("moneycommandai_user_avatar");
      localStorage.removeItem("moneycommandai_user_phone");
      return null;
    }
    const token = localStorage.getItem("moneycommandai_user_token");
    const user_id = localStorage.getItem("moneycommandai_user_id");
    const name  = localStorage.getItem("moneycommandai_user_name");
    return token ? { token, user_id: Number(user_id), name } : null;
  });

  const [showLoginModal, setShowLoginModal]   = useState(false);
  const [showLivePanel,  setShowLivePanel]    = useState(false);
  const [showLiveSuggest, setShowLiveSuggest] = useState(false);
  const [lastUserMsg,    setLastUserMsg]      = useState("");
  const [isMobile, setIsMobile] = useState(() => {
    // URL param is passed by widget.js and reflects the parent page width.
    // Fallback to window.innerWidth for direct browser access.
    const params = new URLSearchParams(window.location.search);
    if (params.has("mobile")) {
      return params.get("mobile") === "true";
    }
    return window.innerWidth <= 480;
  });

  useEffect(() => {
    const handleParentMessage = (e) => {
      if (e.data && e.data.type === 'moneycommandai-parent-resize') {
        setIsMobile(e.data.isMobile);
      }
    };

    const handleLocalResize = () => {
      const params = new URLSearchParams(window.location.search);
      if (!params.has("mobile")) {
        setIsMobile(window.innerWidth <= 480);
      }
    };

    window.addEventListener('message', handleParentMessage);
    window.addEventListener('resize', handleLocalResize);
    return () => {
      window.removeEventListener('message', handleParentMessage);
      window.removeEventListener('resize', handleLocalResize);
    };
  }, []);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Derived state to check if the bot is currently generating a response
  const isGenerating = isTyping || messages.some((msg) => msg.isStreaming);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // CSS close transition durations (must match Chatbot.css .moneycommandai-chat-window transition)
  const CLOSE_ANIM_MS = 350; // slightly longer than the 0.32s transform transition

  useEffect(() => {
    if (open) {
      // Opening: hide the closed-state FAB immediately so it doesn't flash,
      // tell the parent to expand right away, then focus the input.
      setClosedFabReady(false);
      try {
        window.parent.postMessage({ type: "moneycommandai-chatbot-toggle", open: true }, "*");
      } catch (e) {
        console.error("Failed to post toggle message:", e);
      }
      setTimeout(() => inputRef.current?.focus(), 300);
    } else {
      // Closing: let the chat-window CSS transition play out first (CLOSE_ANIM_MS),
      // then restore the closed FAB state and tell the parent to shrink the iframe.
      // This keeps child animation and parent resize perfectly in sync.
      const timer = setTimeout(() => {
        setClosedFabReady(true);
        try {
          window.parent.postMessage({ type: "moneycommandai-chatbot-toggle", open: false }, "*");
        } catch (e) {
          console.error("Failed to post toggle message:", e);
        }
      }, CLOSE_ANIM_MS);
      return () => clearTimeout(timer);
    }
  }, [open]);

  const handleRefreshChat = () => {
    setMessages([]);
    setMessage("");
    setIsTyping(false);
    setShowLiveSuggest(false);
    setShowLivePanel(false);
    setSessionId(Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15));
    fetchConfig();
  };

  function handleAcceptLiveSupport() {
    setShowLiveSuggest(false);
    if (authUser) {
      setShowLivePanel(true);
    } else {
      setShowLoginModal(true);
    }
  }

  function handleLoginSuccess(user) {
    setAuthUser(user);
    setShowLoginModal(false);
    setShowLivePanel(true);
  }

  function handleLogout() {
    localStorage.removeItem("moneycommandai_user_token");
    localStorage.removeItem("moneycommandai_user_id");
    localStorage.removeItem("moneycommandai_user_name");
    localStorage.removeItem("moneycommandai_user_phone");
    localStorage.removeItem("moneycommandai_user_email");
    localStorage.removeItem("moneycommandai_user_avatar");
    setAuthUser(null);
    setShowLivePanel(false);
  }

  const handleSendMessage = async (textToSend) => {
    const trimmed = textToSend.trim();
    if (!trimmed || isGenerating) return;

    const isLiveSupportIntent = [
      "live support",
      "talk to agent",
      "connect to agent",
      "human agent",
      "chat with agent",
      "agent support",
      "live chat",
      "login"
    ].includes(trimmed.toLowerCase());

    if (isLiveSupportIntent) {
      setMessage("");
      if (config.enable_live_support) {
        handleAcceptLiveSupport();
      } else {
        const userMsg = {
          id: Date.now(),
          sender: "user",
          text: trimmed,
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
          })
        };
        const botMsg = {
          id: Date.now() + 1,
          sender: "bot",
          text: "Live support is currently unavailable. How else can I help you?",
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
          })
        };
        setMessages((prev) => [...prev, userMsg, botMsg]);
      }
      return;
    }

    // 1. Add user message
    const userMsg = {
      id: Date.now(),
      sender: "user",
      text: trimmed,
      time: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
      })
    };

    setLastUserMsg(trimmed);
    setShowLiveSuggest(false);

    setMessages((prev) => [...prev, userMsg]);
    setMessage("");
    setIsTyping(true);

    // If matching logging pattern, try local parsing & saving first
    if (isLoggingPattern(trimmed)) {
      try {
        const logResult = await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            window.removeEventListener('message', handleLogMessage);
            reject(new Error('Transaction logging request timed out.'));
          }, 8000);

          function handleLogMessage(event) {
            if (event.data && event.data.type === 'moneycommandai-log-transaction-response') {
              clearTimeout(timeout);
              window.removeEventListener('message', handleLogMessage);
              resolve(event.data.response);
            }
          }

          window.addEventListener('message', handleLogMessage);
          window.parent.postMessage({ type: 'moneycommandai-log-transaction', text: trimmed }, '*');
        });

        if (logResult.status === 'success') {
          setIsTyping(false);
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now() + 1,
              sender: "bot",
              text: logResult.message,
              time: new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit"
              }),
              citations: [],
              suggestions: []
            }
          ]);
          return;
        } else if (logResult.status === 'error') {
          setIsTyping(false);
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now() + 1,
              sender: "bot",
              text: `⚠️ **Logging Failed:** ${logResult.message}`,
              time: new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit"
              }),
              citations: [],
              suggestions: []
            }
          ]);
          return;
        }
      } catch (err) {
        console.warn('[Chatbot] Intercept failed or timed out. Falling back to LLM:', err);
      }
    }

    const localTimeStr = new Date().toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
    const localDayStr = new Date().toLocaleDateString('en-US', {
      weekday: 'long'
    });
    const localDateStr = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    // Build history payload for the backend (excluding the current user message)
    const historyPayload = messages
      .filter((msg) => msg.sender === "user" || msg.sender === "bot")
      .map((msg) => ({
        role: msg.sender === "user" ? "user" : "assistant",
        content: msg.text
      }));

    try {
      const response = await fetch(`${API_BASE}/chat`, {

        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          history: historyPayload,
          local_time: localTimeStr,
          local_day: localDayStr,
          local_date: localDateStr,
          session_id: sessionId,
          user_id: authUser?.user_id || null,
        }),
      });

      if (!response.body) {
        throw new Error("No response body received from API");
      }

      // Keep typing indicator alive until first real token arrives.
      // On real mobile devices, browsers buffer the stream response and
      // reader.read() does not fire until a large enough chunk is received.
      // Without this, an empty blank bubble is shown until the full response flushes.
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;
      let buffer = "";
      let botMsgInitialized = false;

      const botMsgId = Date.now() + 1;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;

        if (value) {
          buffer += decoder.decode(value, { stream: !done });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith("data: ")) {
              try {
                const data = JSON.parse(trimmedLine.slice(6));

                if (data.type === "token") {
                  if (!botMsgInitialized) {
                     // First token received — stop typing indicator and create the bot bubble
                    botMsgInitialized = true;
                    setIsTyping(false);
                    setMessages((prev) => [
                      ...prev,
                      {
                        id: botMsgId,
                        sender: "bot",
                        text: data.content,
                        time: new Date().toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit"
                        }),
                        citations: [],
                        suggestions: [],
                        isStreaming: true
                      }
                    ]);
                  } else {
                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === botMsgId
                          ? { ...msg, text: msg.text + data.content }
                          : msg
                      )
                    );
                  }
                } else if (data.type === "suggestions") {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === botMsgId
                        ? { ...msg, suggestions: data.content }
                        : msg
                    )
                  );
                } else if (data.type === "suggest_live_support") {
                  if (config.enable_live_support) {
                    setShowLiveSuggest(true);
                  }
                } else if (data.type === "citations") {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === botMsgId
                        ? { ...msg, citations: data.content }
                        : msg
                    )
                  );
                } else if (data.type === "done") {
                  // Mark streaming as finished and set the timestamp to the actual response time.
                  // Replace any mention of the request start time in the generated text with this
                  // final response completion time, so they are always in perfect sync.
                  const completedAt = new Date().toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true
                  });
                  setMessages((prev) =>
                    prev.map((msg) => {
                      if (msg.id === botMsgId) {
                        const updatedText = msg.text.replace(localTimeStr, completedAt);
                        return { ...msg, isStreaming: false, time: completedAt, text: updatedText };
                      }
                      return msg;
                    })
                  );
                }
              } catch (err) {
                console.error("Failed to parse SSE JSON chunk:", trimmedLine, err);
              }
            }
          }
        }
      }
    } catch (err) {
      console.error("Connection error:", err);
      setIsTyping(false);

      // Clean up active streaming message if any, and show error
      setMessages((prev) => {
        // Filter out any empty streaming message that failed
        const filtered = prev.filter(m => !(m.sender === "bot" && m.text === ""));
        return [
          ...filtered,
          {
            id: Date.now() + 2,
            sender: "bot",
            text: "Sorry, I'm having trouble connecting right now. Please check if the backend is running and try again.",
            time: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit"
            })
          }
        ];
      });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(message);
    }
  };

  return (
    <div className={isMobile ? "moneycommandai-layout-mobile" : ""}>
      {/* Chat Window */}
      <div className={`moneycommandai-chat-window ${open ? "moneycommandai-chat-window--open" : ""}`}>
        {showLivePanel ? (
          <LiveChatPanel
            token={authUser?.token}
            userId={authUser?.user_id}
            userName={authUser?.name}
            lastPreview={lastUserMsg}
            onClose={() => setShowLivePanel(false)}
            onMinimize={() => setOpen(false)}
          />
        ) : (
          <>
            {/* Header */}
            <div className="moneycommandai-chat-header">
              <div className="moneycommandai-chat-header__border-line"></div>
              <div className="moneycommandai-chat-header__brand">
                <div className="moneycommandai-chat-header__logo">
                  <img
                    src="/chatbot_mascot.png"
                    alt="MoneyCommandAI Assistant Logo"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      display: "block"
                    }}
                  />
                </div>
                <div className="moneycommandai-chat-header__info">
                  <span className="moneycommandai-chat-header__title">MoneyCommandAI Assistant</span>
                  <span className="moneycommandai-chat-header__subtitle">
                    <span className="moneycommandai-chat-header__status-dot"></span>
                    <span>Online</span>
                  </span>
                </div>
              </div>
              <div className="moneycommandai-chat-header__controls">
                <button
                  className="moneycommandai-chat-header__refresh"
                  onClick={handleRefreshChat}
                  aria-label="Refresh chat"
                  title="Refresh chat"
                >
                  <RefreshIcon />
                </button>
                <button
                  className="moneycommandai-chat-header__close"
                  onClick={() => setOpen(false)}
                  aria-label="Close chat"
                >
                  <CloseIcon />
                </button>
              </div>
            </div>

            {/* Messages — or Live Chat Panel */}
            <div className="moneycommandai-chat-messages" id="moneycommandai-chat-messages">
              {messages.length === 0 ? (
                <div className="moneycommandai-chat-home">
                  <div className="moneycommandai-chat-home__text">
                    <h2 className="moneycommandai-chat-home__title">Hello! I'm MoneyCommandAI Assistant</h2>
                    <p className="moneycommandai-chat-home__sub">Ask me anything about ExpenseTracker features, dashboard guides, Telegram bot setup, or how to contact our support team.</p>
                  </div>
                  <div className="moneycommandai-chat-home__chips">
                    {["Telegram Bot Setup", "App Features", "Contact Support"].map((chip) => (
                      <button key={chip} className="moneycommandai-chat-home__chip" onClick={() => handleSendMessage(chip)}>
                        {chip}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div key={msg.id || index} style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                    <div
                      className={`moneycommandai-chat-msg moneycommandai-chat-msg--${msg.sender} ${msg.isStreaming ? "moneycommandai-chat-msg--streaming" : ""}`}
                    >
                      <div className="moneycommandai-chat-msg__bubble">
                        {msg.sender === "bot" ? (
                          <>
                            <BotMessage text={msg.text} />
                            {/* Render Citations inside the bubble */}
                            {msg.citations && msg.citations.length > 0 && (
                              <div className="moneycommandai-chat-citations" id={`citations-${msg.id}`}>
                                <span className="moneycommandai-chat-citations__title">Sources</span>
                                <div className="moneycommandai-chat-citations__list">
                                  {msg.citations.map((cit, idx) => (
                                    <a
                                      key={idx}
                                      href={cit.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="moneycommandai-chat-citation-link"
                                      id={`citation-link-${msg.id}-${idx}`}
                                    >
                                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '4px' }}>
                                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                        <polyline points="15 3 21 3 21 9"></polyline>
                                        <line x1="10" y1="14" x2="21" y2="3"></line>
                                      </svg>
                                      {cit.title.replace(" - MoneyCommandAI Info-Tech", "")}
                                    </a>
                                  ))}
                                </div>
                              </div>
                            )}
                          </>
                        ) : (
                          msg.text
                        )}
                      </div>
                    </div>
                    <div className={`moneycommandai-chat-msg-time-container moneycommandai-chat-msg-time-container--${msg.sender}`}>
                      {msg.time}
                    </div>
                    {/* Render follow-up suggestions below the bubble, only for the latest bot message */}
                    {msg.sender === "bot" &&
                      index === messages.length - 1 &&
                      !msg.isStreaming &&
                      msg.suggestions &&
                      msg.suggestions.length > 0 && (
                        <div className="moneycommandai-chat-suggestions-container" id={`suggestions-${msg.id}`}>
                          {msg.suggestions.map((sug, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSendMessage(sug)}
                              className="moneycommandai-chat-suggestion-chip"
                              id={`suggestion-chip-${msg.id}-${idx}`}
                            >
                              {sug}
                            </button>
                          ))}
                        </div>
                      )}
                  </div>
                ))
              )}

              {/* Typing Indicator */}
              {isTyping && (
                <div className="moneycommandai-chat-msg moneycommandai-chat-msg--bot">
                  <div className="moneycommandai-chat-typing">
                    <span></span>
                    <span></span>
                    <span></span>
                    <small>MoneyCommandAI Assistant is typing...</small>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />

              {/* Live support suggestion card */}
              {showLiveSuggest && (
                <div className="moneycommandai-live-suggest-card" id="moneycommandai-live-suggest-card">
                  <div className="moneycommandai-live-suggest-icon">🎧</div>
                  <div className="moneycommandai-live-suggest-text">
                    <strong>Connect to a live agent?</strong>
                    <span>Our support team is ready to help you right now.</span>
                  </div>
                  <div className="moneycommandai-live-suggest-actions">
                    <button
                      id="moneycommandai-live-suggest-yes"
                      className="moneycommandai-live-suggest-btn moneycommandai-live-suggest-btn--yes"
                      onClick={handleAcceptLiveSupport}
                    >
                      Yes, connect me
                    </button>
                    <button
                      id="moneycommandai-live-suggest-no"
                      className="moneycommandai-live-suggest-btn moneycommandai-live-suggest-btn--no"
                      onClick={() => setShowLiveSuggest(false)}
                    >
                      No, thanks
                    </button>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area — hidden during live chat */}
            <div className="moneycommandai-chat-input-area">
              <input
                ref={inputRef}
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isGenerating ? "Please wait for a response..." : "Ask me anything…"}
                className="moneycommandai-chat-input"
                id="moneycommandai-chat-input"
                disabled={isGenerating}
              />
              <button
                onClick={() => handleSendMessage(message)}
                className={`moneycommandai-chat-send ${message.trim() && !isGenerating ? "moneycommandai-chat-send--active" : ""}`}
                aria-label="Send message"
                id="moneycommandai-chat-send-btn"
                disabled={isGenerating || !message.trim()}
              >
                <SendIcon />
              </button>
            </div>

            <div className="moneycommandai-chat-footer">
              Powered by <span className="moneycommandai-chat-footer__brand">ExpenseTracker</span>
            </div>
          </>
        )}
        {/* Google Login Modal */}
        {showLoginModal && (
          <UserInfoModal
            sessionId={sessionId}
            onSuccess={handleLoginSuccess}
            onClose={() => setShowLoginModal(false)}
          />
        )}
      </div>

      {/* Floating Trigger Button with Tooltip */}
      <div className="moneycommandai-fab-container">
        {/* Tooltip: always rendered in DOM, toggled via CSS visibility classes */}
        <div
          className={`moneycommandai-fab-tooltip ${
            (!open && closedFabReady && showTooltip) ? "moneycommandai-fab-tooltip--visible" : "moneycommandai-fab-tooltip--hidden"
          }`}
          id="moneycommandai-chat-tooltip"
        >
          <span>Ask me anything...</span>
          <button
            className="moneycommandai-fab-tooltip__close"
            onClick={(e) => {
              e.stopPropagation();
              setShowTooltip(false);
            }}
            aria-label="Close tooltip"
          >
            &times;
          </button>
        </div>

        {/* Single FAB — center and position never change, only icon/background swap */}
        <button
          className={`moneycommandai-fab ${open ? "moneycommandai-fab--open" : ""}`}
          onClick={() => setOpen(!open)}
          aria-label={open ? "Close chat" : "Open chat"}
          id="moneycommandai-chat-fab"
        >
          {/* Both icons are mounted at all times to prevent DOM recreation/repaints */}
          <div className="moneycommandai-fab-icon-stack">
            <span className={`moneycommandai-fab-icon-wrapper ${open ? "moneycommandai-fab-icon--hidden" : "moneycommandai-fab-icon--visible"}`}>
              <ChatIcon />
            </span>
            <span className={`moneycommandai-fab-icon-wrapper ${open ? "moneycommandai-fab-icon--visible" : "moneycommandai-fab-icon--hidden"}`}>
              <CloseIcon />
            </span>
          </div>
        </button>
      </div>
    </div>
  );
}
