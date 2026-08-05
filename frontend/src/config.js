/**
 * Centralized URL / environment configuration.
 *
 * VITE_API_URL  – (optional) absolute backend origin for production deploys.
 *                 e.g. "https://api.example.com"
 *                 Leave blank (or unset) in local dev; Vite's dev-server proxy
 *                 will forward /api, /chat, /auth, /agent/* and /socket.io
 *                 requests to the backend automatically.
 */

const rawApiUrl = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

export const API_BASE = rawApiUrl;

export const SOCKET_URL = rawApiUrl || window.location.origin;

export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

export const PERSIST_SESSION = import.meta.env.VITE_PERSIST_SESSION !== "false";
