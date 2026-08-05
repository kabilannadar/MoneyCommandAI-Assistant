import { useState, useEffect, useCallback } from "react";
import "./AdminPanel.css";
import { API_BASE } from "../../config";

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

const EditIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ display: "block" }}>
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
);

const TrashIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ display: "block" }}>
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    <line x1="10" y1="11" x2="10" y2="17" />
    <line x1="14" y1="11" x2="14" y2="17" />
  </svg>
);

// ─── Constants ────────────────────────────────────────────────────────────────
const LS_TOKEN = "moneycommandai_admin_token";

// ─── Helpers ──────────────────────────────────────────────────────────────────
function apiUrl(path) {
  return `${API_BASE}${path}`;
}

async function apiFetch(path, options = {}, token = null) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(apiUrl(path), { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

function handleScroll(e) {
  const el = e.currentTarget;
  el.classList.add("is-scrolling");
  clearTimeout(el._scrollTimer);
  el._scrollTimer = setTimeout(() => {
    el.classList.remove("is-scrolling");
  }, 700);
}

// ─── Toast ────────────────────────────────────────────────────────────────────
function Toast({ message, type, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3000);
    return () => clearTimeout(t);
  }, [onDone]);
  return <div className={`ap-toast ${type}`}>{message}</div>;
}

// ─── Modal ────────────────────────────────────────────────────────────────────
function AgentModal({ agent, onClose, onSave, token }) {
  const isEdit = Boolean(agent?.id);
  const [form, setForm] = useState({
    name:       agent?.name       || "",
    email:      agent?.email      || "",
    password:   "",
    avatar_url: agent?.avatar_url || "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [confirmText, setConfirmText] = useState("");

  const isNameFilled = form.name.trim().length > 0;
  const isEmailFilled = form.email.trim().length > 0;
  const isPasswordFilledIfRequired = isEdit ? true : form.password.length > 0;
  const passwordsMatch = form.password === confirmPassword;
  const confirmTextMatches = confirmText === "confirm";
  const isFormSubmittable = isNameFilled && isEmailFilled && isPasswordFilledIfRequired && passwordsMatch && confirmTextMatches;

  function set(k, v) { setForm(f => ({ ...f, [k]: v })); }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!isFormSubmittable) return;
    setLoading(true);
    setError("");
    try {
      let saved;
      if (isEdit) {
        const payload = {};
        if (form.name)       payload.name       = form.name;
        if (form.email)      payload.email      = form.email;
        if (form.password)   payload.password   = form.password;
        if (form.avatar_url !== undefined) payload.avatar_url = form.avatar_url;
        saved = await apiFetch(`/admin/agents/${agent.id}`, { method: "PATCH", body: JSON.stringify(payload) }, token);
      } else {
        saved = await apiFetch("/admin/agents", { method: "POST", body: JSON.stringify(form) }, token);
      }
      onSave(saved);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ap-modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="ap-modal">
        <div className="ap-modal-header">
          <h3>{isEdit ? "Edit Agent" : "Add New Agent"}</h3>
          <button className="ap-modal-close" onClick={onClose}>✕</button>
        </div>

        {error && <div className="ap-error">{error}</div>}

        <form className="ap-modal-form" onSubmit={handleSubmit}>
          <div className="ap-field">
            <label>Full Name</label>
            <input value={form.name} onChange={e => set("name", e.target.value)}
              placeholder="Agent Name" required={!isEdit} />
          </div>
          <div className="ap-field">
            <label>Email Address</label>
            <input type="email" value={form.email} onChange={e => set("email", e.target.value)}
              placeholder="agent@moneycommandai.in" required={!isEdit} />
          </div>
          <div className="ap-field">
            <label>{isEdit ? "New Password (leave blank to keep it unchanged)" : "Password"}</label>
            <div className="ap-password-wrapper" style={{ position: "relative", width: "100%" }}>
              <input type={showPassword ? "text" : "password"} value={form.password} onChange={e => set("password", e.target.value)}
                placeholder={isEdit ? "••••••••" : "Enter password"} required={!isEdit} style={{ paddingRight: "2.75rem", width: "100%" }} />
              <button
                type="button"
                className="ap-password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                style={{
                  position: "absolute",
                  right: "12px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "#5a7089",
                  padding: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  zIndex: 2
                }}
              >
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            </div>
          </div>
          <div className="ap-field">
            <label>Confirm Password</label>
            <div className="ap-password-wrapper" style={{ position: "relative", width: "100%" }}>
              <input
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Confirm password"
                required={form.password.length > 0}
                style={{ paddingRight: "2.75rem", width: "100%" }}
              />
              <button
                type="button"
                className="ap-password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                style={{
                  position: "absolute",
                  right: "12px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "#5a7089",
                  padding: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  zIndex: 2
                }}
              >
                {showConfirmPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            </div>
            {form.password && confirmPassword && form.password !== confirmPassword && (
              <span style={{ color: "var(--ap-danger)", fontSize: "0.75rem", marginTop: "0.25rem" }}>
                Passwords do not match.
              </span>
            )}
          </div>
          <div className="ap-field">
            <label>Avatar URL (optional)</label>
            <input value={form.avatar_url} onChange={e => set("avatar_url", e.target.value)}
              placeholder="https://…" />
          </div>
          <div className="ap-field">
            <label>Type <strong style={{ color: "var(--ap-danger)" }}>confirm</strong> to save changes</label>
            <input
              type="text"
              value={confirmText}
              onChange={e => setConfirmText(e.target.value)}
              placeholder="Type 'confirm'"
              onPaste={e => e.preventDefault()}
              onDrop={e => e.preventDefault()}
              required
            />
          </div>
          <div className="ap-modal-actions">
            <button type="button" className="ap-btn ap-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="ap-btn ap-btn-primary" disabled={loading || !isFormSubmittable}>
              {loading ? <span className="ap-spinner" /> : isEdit ? "Save Changes" : "Create Agent"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Delete Confirm Modal ─────────────────────────────────────────────────────
function DeleteModal({ agent, onClose, onDelete }) {
  return (
    <div className="ap-modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="ap-modal" style={{ width: 380 }}>
        <div className="ap-modal-header">
          <h3>Delete Agent</h3>
          <button className="ap-modal-close" onClick={onClose}>✕</button>
        </div>
        <p style={{ fontSize: "0.875rem", color: "var(--ap-muted)", lineHeight: 1.6 }}>
          Are you sure you want to permanently delete <strong style={{ color: "var(--ap-text)" }}>{agent.name}</strong>?
          This action cannot be undone.
        </p>
        <div className="ap-modal-actions">
          <button className="ap-btn ap-btn-secondary" onClick={onClose}>Cancel</button>
          <button className="ap-btn ap-btn-danger" onClick={() => onDelete(agent.id)}>Delete</button>
        </div>
      </div>
    </div>
  );
}

// ─── Feature Flags Tab ────────────────────────────────────────────────────────
function FlagsTab({ token, onToast }) {
  const [flags, setFlags]   = useState(null);
  const [saving, setSaving] = useState(null); // which key is saving

  const load = useCallback(async () => {
    try {
      const data = await apiFetch("/admin/config", {}, token);
      setFlags(data);
    } catch (err) {
      onToast(err.message, "error");
    }
  }, [token, onToast]);

  useEffect(() => { load(); }, [load]);

  async function toggle(key, value) {
    setSaving(key);
    try {
      const data = await apiFetch("/admin/config", {
        method: "POST",
        body: JSON.stringify({ [key]: value }),
      }, token);
      setFlags(data);
      onToast("Setting updated", "success");
    } catch (err) {
      onToast(err.message, "error");
    } finally {
      setSaving(null);
    }
  }

  if (!flags) return <div className="ap-empty"><span className="ap-spinner" /></div>;

  const DEFS = [
    {
      key:   "enable_rag",
      label: "Enable RAG",
      desc:  "Retrieval-Augmented Generation — lets the chatbot answer questions from your uploaded documents and website content.",
    },
    {
      key:   "enable_live_support",
      label: "Enable Live Support",
      desc:  "Show the 'Talk to a human' option in the chatbot so users can connect with a support agent in real time.",
    },
    {
      key:   "persist_session",
      label: "Persist Session",
      desc:  "Keep users logged in across page reloads. When OFF, sessions reset on every page visit.",
    },
  ];

  return (
    <>
      <div className="ap-page-header">
        <h2>Feature Flags</h2>
        <p>Toggle features on or off — changes apply immediately.</p>
      </div>
      <div className="ap-flags-grid">
        {DEFS.map(({ key, label, desc }) => {
          const isOn  = flags[key];
          const isSaving = saving === key;
          return (
            <div key={key} className={`ap-flag-card ${isOn ? "enabled" : ""}`}>
              <div className="ap-flag-body">
                <h3>{label}</h3>
                <p>{desc}</p>
              </div>
              <label className="ap-toggle">
                <input type="checkbox" checked={isOn} disabled={isSaving}
                  onChange={e => toggle(key, e.target.checked)} />
                <span className="ap-toggle-track" />
              </label>
            </div>
          );
        })}
      </div>
    </>
  );
}

// ─── Agents Tab ───────────────────────────────────────────────────────────────
function AgentsTab({ token, onToast }) {
  const [agents, setAgents]         = useState([]);
  const [loading, setLoading]       = useState(true);
  const [modal, setModal]           = useState(null); // null | { mode: "add"|"edit", agent? }
  const [deleteTarget, setDeleteTarget] = useState(null);

  const load = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    try {
      const data = await apiFetch("/admin/agents", {}, token);
      setAgents(data);
    } catch (err) {
      if (!isSilent) onToast(err.message, "error");
    } finally {
      if (!isSilent) setLoading(false);
    }
  }, [token, onToast]);

  useEffect(() => {
    load(false);
    const interval = setInterval(() => {
      load(true);
    }, 4000); // silent polling every 4 seconds
    return () => clearInterval(interval);
  }, [load]);

  async function handleDelete(id) {
    try {
      await apiFetch(`/admin/agents/${id}`, { method: "DELETE" }, token);
      setAgents(prev => prev.filter(a => a.id !== id));
      setDeleteTarget(null);
      onToast("Agent deleted", "success");
    } catch (err) {
      onToast(err.message, "error");
    }
  }

  function handleSaved(saved) {
    setAgents(prev => {
      const idx = prev.findIndex(a => a.id === saved.id);
      if (idx >= 0) { const n = [...prev]; n[idx] = saved; return n; }
      return [...prev, saved];
    });
    setModal(null);
    onToast(saved ? "Agent saved" : "Agent created", "success");
  }

  return (
    <>
      <div className="ap-page-header">
        <h2>Support Agents</h2>
        <p>Manage the support team who handle live chat sessions.</p>
      </div>

      <div className="ap-agents-header">
        <span style={{ fontSize: "0.875rem", color: "var(--ap-muted)" }}>
          {agents.length} agent{agents.length !== 1 ? "s" : ""}
        </span>
        <button className="ap-btn ap-btn-primary" onClick={() => setModal({ mode: "add" })}>
          + Add Agent
        </button>
      </div>

      <div className="ap-table-wrap" onScroll={handleScroll}>
        {loading ? (
          <div className="ap-empty"><span className="ap-spinner" /></div>
        ) : agents.length === 0 ? (
          <div className="ap-empty">No agents yet. Add one above.</div>
        ) : (
          <table className="ap-table">
            <colgroup>
              <col style={{ width: "30%" }} />
              <col style={{ width: "40%" }} />
              <col style={{ width: "18%" }} />
              <col style={{ width: "12%" }} />
            </colgroup>
            <thead>
              <tr>
                <th>Agent</th>
                <th>Email</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {agents.map(agent => (
                <tr key={agent.id}>
                  <td className="ellipsis">
                    <div className="ap-agent-cell">
                      <div className="ap-agent-avatar">
                        {agent.avatar_url
                          ? <img src={agent.avatar_url} alt={agent.name} />
                          : agent.name.charAt(0).toUpperCase()}
                      </div>
                      <span>{agent.name}</span>
                    </div>
                  </td>
                  <td className="ellipsis" style={{ color: "var(--ap-muted)" }} title={agent.email}>{agent.email}</td>
                  <td>
                    <span className={`ap-badge ${agent.is_online ? "online" : "offline"}`}>
                      <span className={`ap-status-dot ${agent.is_online ? "online" : "offline"}`} />
                      {agent.is_online ? "Online" : "Offline"}
                    </span>
                  </td>
                  <td>
                    <div className="ap-row-actions">
                      <button className="ap-icon-btn edit"
                        title="Edit" onClick={() => setModal({ mode: "edit", agent })}>
                        <EditIcon />
                      </button>
                      <button className="ap-icon-btn delete"
                        title="Delete" onClick={() => setDeleteTarget(agent)}>
                        <TrashIcon />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modal && (
        <AgentModal
          agent={modal.agent}
          token={token}
          onClose={() => setModal(null)}
          onSave={handleSaved}
        />
      )}
      {deleteTarget && (
        <DeleteModal
          agent={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDelete={handleDelete}
        />
      )}
    </>
  );
}

// ─── Login Page ───────────────────────────────────────────────────────────────
function LoginPage({ onLogin }) {
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch("/admin/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem(LS_TOKEN, data.token);
      onLogin(data.token, data.email);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ap-login-page">
      <div className="ap-login-card">
        <div className="ap-login-logo">
          <div className="ap-login-title-group">
            <h1>MoneyCommandAI Admin</h1>
            <p>Superadmin Control Panel</p>
          </div>
        </div>

        <h2>Welcome back</h2>

        {error && <div className="ap-error">{error}</div>}

        <form className="ap-login-form" onSubmit={handleSubmit}>
          <div className="ap-field">
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="superadmin@moneycommandai.in" required autoFocus />
          </div>
          <div className="ap-field">
            <label>Password</label>
            <div className="ap-password-wrapper" style={{ position: "relative", width: "100%" }}>
              <input type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)}
                placeholder="••••••••" required style={{ paddingRight: "2.75rem", width: "100%" }} />
              <button
                type="button"
                className="ap-password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                style={{
                  position: "absolute",
                  right: "12px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "#5a7089",
                  padding: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  zIndex: 2
                }}
              >
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            </div>
          </div>
          <button type="submit" className="ap-btn ap-btn-primary" disabled={loading} style={{ marginTop: "0.25rem" }}>
            {loading ? <span className="ap-spinner" /> : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─── User Modals & Tab ───────────────────────────────────────────────────────
function UserModal({ user, onClose, onSave, token }) {
  const isEdit = Boolean(user?.id);
  const [form, setForm] = useState({
    name:  user?.name  || "",
    phone: user?.phone || "",
    email: user?.email || "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  function set(k, v) { setForm(f => ({ ...f, [k]: v })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      let saved;
      if (isEdit) {
        saved = await apiFetch(`/admin/users/${user.id}`, { method: "PATCH", body: JSON.stringify(form) }, token);
      } else {
        saved = await apiFetch("/admin/users", { method: "POST", body: JSON.stringify(form) }, token);
      }
      onSave(saved);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ap-modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="ap-modal">
        <div className="ap-modal-header">
          <h3>{isEdit ? "Edit User" : "Add New User"}</h3>
          <button className="ap-modal-close" onClick={onClose}>✕</button>
        </div>

        {error && <div className="ap-error">{error}</div>}

        <form className="ap-modal-form" onSubmit={handleSubmit}>
          <div className="ap-field">
            <label>Full Name</label>
            <input value={form.name} onChange={e => set("name", e.target.value)} placeholder="User Name" />
          </div>
          <div className="ap-field">
            <label>Phone Number</label>
            <input value={form.phone} onChange={e => set("phone", e.target.value)} placeholder="9022879379" />
          </div>
          <div className="ap-field">
            <label>Email Address</label>
            <input type="email" value={form.email} onChange={e => set("email", e.target.value)} placeholder="user@example.com" />
          </div>
          <div className="ap-modal-actions">
            <button type="button" className="ap-btn ap-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="ap-btn ap-btn-primary" disabled={loading}>
              {loading ? <span className="ap-spinner" /> : isEdit ? "Save Changes" : "Create User"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function UserDeleteModal({ user, onClose, onDelete }) {
  return (
    <div className="ap-modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="ap-modal" style={{ width: 420 }}>
        <div className="ap-modal-header">
          <h3>Delete User Account</h3>
          <button className="ap-modal-close" onClick={onClose}>✕</button>
        </div>
        <p style={{ fontSize: "0.875rem", color: "var(--ap-muted)", lineHeight: 1.6 }}>
          Are you sure you want to delete <strong style={{ color: "var(--ap-text)" }}>{user.name || user.phone || `User #${user.id}`}</strong>?
          <br /><br />
          <span style={{ color: "var(--ap-danger)", fontWeight: "600" }}>
            ⚠️ Deleting this user will automatically purge all associated chat sessions, live support sessions, and message logs from the database.
          </span>
        </p>
        <div className="ap-modal-actions">
          <button className="ap-btn ap-btn-secondary" onClick={onClose}>Cancel</button>
          <button className="ap-btn ap-btn-danger" onClick={() => onDelete(user.id)}>Delete User & Data</button>
        </div>
      </div>
    </div>
  );
}

function UsersTab({ token, onToast }) {
  const [users, setUsers]               = useState([]);
  const [search, setSearch]             = useState("");
  const [loading, setLoading]           = useState(true);
  const [modal, setModal]               = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const load = useCallback(async (query = "") => {
    setLoading(true);
    try {
      const url = query ? `/admin/users?search=${encodeURIComponent(query)}` : "/admin/users";
      const data = await apiFetch(url, {}, token);
      setUsers(data);
    } catch (err) {
      onToast(err.message, "error");
    } finally {
      setLoading(false);
    }
  }, [token, onToast]);

  useEffect(() => { load(search); }, [load, search]);

  async function handleDelete(id) {
    try {
      await apiFetch(`/admin/users/${id}`, { method: "DELETE" }, token);
      setUsers(prev => prev.filter(u => u.id !== id));
      setDeleteTarget(null);
      onToast("User and all associated data deleted", "success");
    } catch (err) {
      onToast(err.message, "error");
    }
  }

  function handleSaved(saved) {
    setUsers(prev => {
      const idx = prev.findIndex(u => u.id === saved.id);
      if (idx >= 0) { const n = [...prev]; n[idx] = saved; return n; }
      return [saved, ...prev];
    });
    setModal(null);
    onToast("User saved successfully", "success");
  }

  return (
    <>
      <div className="ap-page-header">
        <h2>User Accounts</h2>
        <p>Manage customer profiles, search accounts, and update user credentials.</p>
      </div>

      <div className="ap-agents-header">
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flex: 1, maxWidth: 360 }}>
          <input
            type="text"
            style={{
              padding: "0.6rem 0.85rem",
              fontSize: "0.875rem",
              borderRadius: "var(--ap-radius-sm)",
              border: "1.5px solid var(--ap-border)",
              width: "100%",
              outline: "none",
              background: "var(--ap-surface)",
              color: "var(--ap-text)"
            }}
            placeholder="Search name, phone, email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <button className="ap-btn ap-btn-primary" onClick={() => setModal({ mode: "add" })}>
          + Add User
        </button>
      </div>

      <div className="ap-table-wrap" onScroll={handleScroll}>
        {loading ? (
          <div className="ap-empty"><span className="ap-spinner" /></div>
        ) : users.length === 0 ? (
          <div className="ap-empty">No users found.</div>
        ) : (
          <table className="ap-table">
            <colgroup>
              <col style={{ width: "24%" }} />
              <col style={{ width: "18%" }} />
              <col style={{ width: "30%" }} />
              <col style={{ width: "14%" }} />
              <col style={{ width: "14%" }} />
            </colgroup>
            <thead>
              <tr>
                <th>User</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Sessions</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td className="ellipsis">
                    <div className="ap-agent-cell">
                      <div className="ap-agent-avatar">
                        {(u.name || u.phone || "U").charAt(0).toUpperCase()}
                      </div>
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        <span style={{ fontWeight: 600 }}>{u.name || "Unnamed User"}</span>
                        <span style={{ fontSize: "0.72rem", color: "var(--ap-muted)" }}>ID #{u.id}</span>
                      </div>
                    </div>
                  </td>
                  <td className="ellipsis" style={{ color: "var(--ap-text-sec)" }}>{u.phone || "—"}</td>
                  <td className="ellipsis" style={{ color: "var(--ap-muted)" }} title={u.email || ""}>{u.email || "—"}</td>
                  <td>
                    <span className="ap-badge online" style={{ background: "var(--ap-accent-lt)", color: "var(--ap-accent)" }}>
                      {u.session_count} Session{u.session_count !== 1 ? "s" : ""}
                    </span>
                  </td>
                  <td>
                    <div className="ap-row-actions">
                      <button className="ap-icon-btn edit" title="Edit" onClick={() => setModal({ mode: "edit", user: u })}>
                        <EditIcon />
                      </button>
                      <button className="ap-icon-btn delete" title="Delete" onClick={() => setDeleteTarget(u)}>
                        <TrashIcon />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modal && (
        <UserModal
          user={modal.user}
          token={token}
          onClose={() => setModal(null)}
          onSave={handleSaved}
        />
      )}
      {deleteTarget && (
        <UserDeleteModal
          user={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDelete={handleDelete}
        />
      )}
    </>
  );
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
const TABS = [
  { id: "users",  label: "Users" },
  { id: "agents", label: "Agents" },
  { id: "flags",  label: "Feature Flags" },
];

function Dashboard({ token, email, onLogout }) {
  const [tab, setTab]   = useState("users");
  const [toast, setToast] = useState(null);

  function showToast(message, type = "success") {
    setToast({ message, type, key: Date.now() });
  }

  return (
    <div className="ap-dashboard">
      {/* Sidebar */}
      <aside className="ap-sidebar">
        <div className="ap-sidebar-logo">
          <span>MoneyCommandAI Admin</span>
        </div>

        <div className="ap-sidebar-nav" onScroll={handleScroll}>
          {TABS.map(t => (
            <button key={t.id} className={`ap-nav-item ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>

        <div className="ap-sidebar-footer">
          <div className="ap-sidebar-user">Signed in as<br /><strong>{email}</strong></div>
          <button className="ap-nav-item" style={{ marginTop: "0.5rem", color: "var(--ap-danger)" }}
            onClick={onLogout}>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="ap-main">
        <div className="ap-content-container">
          <div key={tab} className="ap-tab-content">
            {tab === "flags"  && <FlagsTab  token={token} onToast={showToast} />}
            {tab === "agents" && <AgentsTab token={token} onToast={showToast} />}
            {tab === "users"  && <UsersTab  token={token} onToast={showToast} />}
          </div>
        </div>
      </main>

      {toast && (
        <Toast key={toast.key} message={toast.message} type={toast.type}
          onDone={() => setToast(null)} />
      )}
    </div>
  );
}

// ─── Root ─────────────────────────────────────────────────────────────────────
export default function AdminPanel() {
  const [token, setToken] = useState(() => localStorage.getItem(LS_TOKEN) || "");
  const [email, setEmail] = useState("");

  // Verify stored token on mount
  useEffect(() => {
    if (!token) return;
    apiFetch("/admin/me", {}, token)
      .then(d => setEmail(d.email))
      .catch(() => {
        localStorage.removeItem(LS_TOKEN);
        setToken("");
      });
  }, [token]);

  function handleLogin(tok, em) {
    setToken(tok);
    setEmail(em);
  }

  async function handleLogout() {
    try {
      await apiFetch("/admin/logout", { method: "POST" }, token);
    } catch (err) {
      console.error("Failed to notify backend of admin logout:", err);
    }
    localStorage.removeItem(LS_TOKEN);
    setToken("");
    setEmail("");
  }

  return (
    <div className="ap-root">
      {token && email
        ? <Dashboard token={token} email={email} onLogout={handleLogout} />
        : <LoginPage onLogin={handleLogin} />}
    </div>
  );
}
