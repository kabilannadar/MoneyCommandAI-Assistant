import { useState } from "react";
import "./UserInfoModal.css";
import { API_BASE } from "../../config";

export default function UserInfoModal({ sessionId, onSuccess, onClose }) {
  const [phone, setPhone] = useState("");
  const [name, setName]   = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const trimmedPhone = phone.trim().replace(/\s+/g, "");
    if (!trimmedPhone) {
      setError("Phone number is required.");
      return;
    }
    // Exactly 10 digits required (strips +, spaces, dashes before counting)
    const digitsOnly = trimmedPhone.replace(/[^\d]/g, "");
    if (digitsOnly.length !== 10) {
      setError("Phone number must be exactly 10 digits.");
      return;
    }

    const trimmedEmail = email.trim();
    if (trimmedEmail) {
      const emailRegex = /^[^\s@]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,6}$/;
      if (!emailRegex.test(trimmedEmail)) {
        console.warn("[Validation] Invalid email format:", trimmedEmail);
        setError("Please enter a valid email address (e.g. name@domain.com).");
        return;
      }
    }



    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/phone-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone:      trimmedPhone,
          name:       name.trim()  || null,
          email:      email.trim() || null,
          session_id: sessionId    || null,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication failed. Please try again.");
      }

      // Persist user session details
      localStorage.setItem("moneycommandai_user_token", data.token);
      localStorage.setItem("moneycommandai_user_id",    String(data.user_id));
      localStorage.setItem("moneycommandai_user_name",  data.name || "");
      localStorage.setItem("moneycommandai_user_phone", data.phone);
      if (data.email) {
        localStorage.setItem("moneycommandai_user_email", data.email);
      } else {
        localStorage.removeItem("moneycommandai_user_email");
      }

      onSuccess({
        token:   data.token,
        userId:  data.user_id,
        name:    data.name || "",
        phone:   data.phone,
        email:   data.email || ""
      });
    } catch (err) {
      console.error("[UserInfoModal Auth Error]", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="uim-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="uim-card">
        {/* Close */}
        <button className="uim-close" onClick={onClose} aria-label="Close modal">
          ✕
        </button>

        {/* Header */}
        <div className="uim-header">
          <div className="uim-icon-wrap">🎧</div>
          <h2 className="uim-title">Talk to an agent</h2>
          <p className="uim-subtitle">
            Provide your details so we can assign you to a support agent.
          </p>
        </div>

        {/* Error Notification */}
        {error && <div className="uim-error">{error}</div>}

        {/* Form */}
        <form className="uim-form" onSubmit={handleSubmit}>
          {/* Phone */}
          <div className="uim-field">
            <label className="uim-label" htmlFor="uim-phone-input">
              Phone Number <span className="uim-req">*</span>
            </label>
            <div className="uim-input-wrap">
              <span className="uim-phone-prefix">🇮🇳</span>
              <input
                id="uim-phone-input"
                type="tel"
                placeholder="10-digit number"
                className="uim-input uim-input--phone"
                value={phone}
                onChange={(e) => {
                  const val = e.target.value.replace(/[^\d]/g, "");
                  if (val.length <= 10) {
                    setPhone(val);
                  }
                }}
                autoComplete="tel"
                disabled={loading}
                maxLength={10}
              />
            </div>
          </div>

          {/* Name */}
          <div className="uim-field">
            <label className="uim-label" htmlFor="uim-name-input">
              Name <span className="uim-opt">(optional)</span>
            </label>
            <input
              id="uim-name-input"
              type="text"
              placeholder="Your full name"
              className="uim-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              disabled={loading}
            />
          </div>

          {/* Email */}
          <div className="uim-field">
            <label className="uim-label" htmlFor="uim-email-input">
              Email Address <span className="uim-opt">(optional)</span>
            </label>
            <input
              id="uim-email-input"
              type="email"
              placeholder="name@example.com"
              className="uim-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              disabled={loading}
            />
          </div>

          {/* Submit */}
          <button
            id="uim-submit-btn"
            type="submit"
            className="uim-submit"
            disabled={loading}
          >
            {loading ? <span className="uim-spinner" /> : "Connect Now →"}
          </button>
        </form>

        <p className="uim-privacy">
          Your information is secure and only used for support routing.
        </p>
      </div>
    </div>
  );
}
