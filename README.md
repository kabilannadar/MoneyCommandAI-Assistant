<div align="center">

  <img src="https://raw.githubusercontent.com/kabilannadar/MoneyCommandAI-Assistant/main/frontend/public/MoneyCommandAI_Chatbot_Banner.png" alt="MoneyCommandAI Assistant Banner" width="100%" />

  <h1>MoneyCommandAI Assistant</h1>

  <p><strong>The smart AI support layer embedded inside <a href="https://expensetrackertn.vercel.app">ExpenseTracker</a> — helping users master their personal finances via natural language chat.</strong></p>

  <!-- Badges -->
  <p>
    <a href="https://github.com/kabilannadar/MoneyCommandAI-Assistant/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/license-Proprietary-red?style=flat-square" alt="License" />
    </a>
    <a href="https://github.com/kabilannadar/MoneyCommandAI-Assistant/actions">
      <img src="https://img.shields.io/github/actions/workflow/status/kabilannadar/MoneyCommandAI-Assistant/keep_alive.yml?label=keep-alive&style=flat-square" alt="Keep Alive" />
    </a>
    <img src="https://img.shields.io/badge/python-3.11-blue?style=flat-square&logo=python" alt="Python 3.11" />
    <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react" alt="React 19" />
    <img src="https://img.shields.io/badge/Vite-8-646CFF?style=flat-square&logo=vite" alt="Vite 8" />
    <img src="https://img.shields.io/badge/LLM-Groq-FF6B00?style=flat-square" alt="Groq LLM" />
    <img src="https://img.shields.io/badge/Vector_DB-ChromaDB-6C3483?style=flat-square" alt="ChromaDB" />
    <img src="https://img.shields.io/badge/Socket.IO-realtime-010101?style=flat-square&logo=socket.io" alt="Socket.IO" />
    <img src="https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker" alt="Docker" />
  </p>

  <!-- Quick Links -->
  <p>
    <a href="https://expensetrackertn.vercel.app"><strong>🌐 Live App</strong></a>
    &nbsp;•&nbsp;
    <a href="https://expensetrackertn.vercel.app/support"><strong>💬 Support & Feedback</strong></a>
    &nbsp;•&nbsp;
    <a href="https://t.me/expensetrackertnbot"><strong>🤖 Telegram Bot</strong></a>
    &nbsp;•&nbsp;
    <a href="#getting-started"><strong>🚀 Get Started</strong></a>
    &nbsp;•&nbsp;
    <a href="#api-reference"><strong>📖 API Docs</strong></a>
  </p>

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Embeddable Widget](#embeddable-widget)
- [Admin Panel](#admin-panel)
- [Agent Dashboard](#agent-dashboard)
- [Live Support System](#live-support-system)
- [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
- [Docker Deployment](#docker-deployment)
- [CI/CD — Keep Alive Workflow](#cicd--keep-alive-workflow)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**MoneyCommandAI Assistant** is a production-grade, full-stack AI chatbot application built to serve as the intelligent support layer for the ExpenseTracker personal finance platform. It helps users understand app features, set up Telegram bot logging, manage budgets/goals/reminders, and escalate to live human agents when needed.

The system is composed of:

- A **FastAPI** backend with streaming SSE responses, Socket.IO real-time communication, JWT authentication, and a SQLite/PostgreSQL database.
- A **React** (Vite) frontend that renders the chat interface, an agent dashboard, and an admin panel.
- An **embeddable JavaScript widget** (`widget.js`) that injects the chatbot into any third-party webpage via a single `<script>` tag.

---

## Features

### 🤖 AI Chatbot

- Powered by **Groq LLM** (fast inference) with a carefully engineered system prompt.
- **Intent detection** classifies user queries into categories (`GREETING`, `TELEGRAM_SETUP`, `TELEGRAM_LOGGING`, `APP_FEATURES`, `SUPPORT_CONTACT`) to inject the most relevant context into the prompt.
- **Response streaming** via Server-Sent Events (SSE) for a smooth, real-time typing effect.
- **Conversation cache** avoids redundant LLM calls for repeated identical queries.
- **Follow-up suggestions** are generated alongside each response.
- **Citation streaming** — sources from web search are returned alongside answers.

### 🔍 RAG (Retrieval-Augmented Generation)

- Optional semantic knowledge base powered by **ChromaDB** and **Hugging Face** embeddings (`all-MiniLM-L6-v2`).
- When enabled (`ENABLE_RAG=true`), relevant help documents are retrieved and injected into the LLM context, reducing hallucinations.
- Falls back gracefully if RAG is unavailable.

### 🌐 Web Search Fallback

- If the local RAG knowledge base does not have enough context, the chatbot can optionally perform a **DuckDuckGo web search** (`ddgs`) scoped to finance-related topics.
- Search is gated by a topic-scope check so it only fires for relevant queries.

### 🔒 Safety Filters

- **Vulgar content detection** blocks offensive input before it reaches the LLM.
- **Negative sentiment detection** triggers an empathetic response flow rather than escalating abusive messages.

### 💬 Live Human Support

- Real-time user to agent messaging over **Socket.IO**.
- Users can request to escalate from AI chat to a live human agent.
- A **waiting queue** is maintained and broadcast to all connected agents.
- Agents can claim, chat with, and resolve sessions from the Agent Dashboard.
- Stale "waiting" sessions are automatically resolved on server restart.
- Reliable page-unload cleanup via `navigator.sendBeacon` to the `/api/live/cancel-queue` endpoint.

### 👤 Authentication

- **Google Sign-In** (OAuth 2.0 via `@react-oauth/google`) for end users.
- **Phone-based login** for users.
- **JWT-based** session management for users, support agents, and admins.

### 🛡️ Rate Limiting

- Chat endpoint: **30 requests / 60 seconds** per IP.
- Auth endpoints (`/auth/phone-login`, `/agent/login`, `/admin/login`): **5 attempts / 10 minutes** per IP.

### ⚙️ Admin Panel

- Manage support agents (create, update, delete).
- Configure dynamic settings (enable/disable RAG, live support, session persistence) that take effect without a server restart.
- View and manage registered users.

### 🔌 Embeddable Widget

- Drop-in `<script>` tag that injects an iframe-based chatbot into any website.
- Responsive across mobile (fullscreen), tablet, and desktop.
- Auto-resizes and communicates with the parent page via `postMessage`.

---

## Architecture

```
+-------------------------------------------------------------+
|                    Browser / Host Page                      |
|   +------------------------------------------------------+  |
|   |             React Frontend (Vite)                    |  |
|   |   +----------+  +----------------+  +-------------+ |  |
|   |   | Chatbot  |  | Agent Dashboard|  | Admin Panel | |  |
|   |   +----------+  +----------------+  +-------------+ |  |
|   +------------------------------------------------------+  |
|         | HTTP + SSE            | Socket.IO                  |
+---------|----------------------|-----------------------------|
          |                      |
+---------v----------------------v-----------------------------+
|                FastAPI Backend (Uvicorn)                     |
|   +-------------+  +-----------+  +----------------------+  |
|   | /chat (SSE) |  | Auth APIs |  | Socket.IO (LiveChat) |  |
|   +------+------+  +-----------+  +----------------------+  |
|          |                                                   |
|   +------v------+  +-----------+  +----------------------+  |
|   |  Chatbot    |  |    RAG    |  |    Admin Config DB   |  |
|   |  Engine     |  | ChromaDB  |  | (SQLite/PostgreSQL)  |  |
|   +------+------+  +-----+-----+  +----------------------+  |
|          |               |                                   |
|   +------v---------------v------+                           |
|   |        Groq LLM API         |                           |
|   +------------------------------+                          |
+-------------------------------------------------------------+
```

---

## Project Structure

```
MoneyCommandAI/
|-- backend/
|   |-- auth/                    # Authentication routers
|   |   |-- auth.py              # User auth (Google OAuth, phone login)
|   |   |-- agent_auth.py        # Support agent login/auth
|   |   |-- admin_auth.py        # Admin login/auth
|   |   |-- admin_agents.py      # Agent management APIs
|   |   |-- admin_config.py      # Dynamic config settings APIs
|   |   `-- admin_users.py       # User management APIs
|   |-- chatbot/
|   |   |-- chatbot.py           # Core streaming response generator
|   |   |-- intent.py            # Query intent classifier
|   |   |-- prompts.py           # System prompt builder (intent-aware)
|   |   |-- prompt_blocks.py     # Modular prompt block components
|   |   |-- data.py              # Static knowledge data
|   |   |-- cache.py             # In-memory response cache
|   |   |-- security.py          # Vulgar/negative content filters
|   |   |-- responses.py         # Standard blocked-response strings
|   |   `-- web_search.py        # DuckDuckGo fallback search
|   |-- db/
|   |   |-- database.py          # Async SQLAlchemy engine and session
|   |   `-- models.py            # ORM models (users, sessions, agents, etc.)
|   |-- live/
|   |   |-- live_chat.py         # Socket.IO event handlers
|   |   |-- sio_instance.py      # Shared Socket.IO server instance
|   |   `-- state.py             # In-memory queue and session state
|   |-- rag/
|   |   |-- rag.py               # ChromaDB retrieval + HF embeddings
|   |   `-- ingest.py            # Document ingestion pipeline
|   |-- utils/
|   |   `-- logger.py            # Centralized logging setup
|   |-- config.py                # Groq client + dynamic env var access
|   |-- keep_alive.py            # Self-ping script for free-tier hosting
|   |-- main.py                  # FastAPI app, middleware, routes
|   `-- requirements.txt
|
|-- frontend/
|   |-- public/
|   |   `-- widget.js            # Drop-in embeddable chatbot widget
|   |-- src/
|   |   |-- components/
|   |   |   |-- Chatbot/         # Main chat UI component
|   |   |   |-- LiveChatPanel/   # Live support chat panel
|   |   |   `-- UserInfoModal/   # User info collection modal
|   |   |-- pages/
|   |   |   |-- AdminPanel/      # Admin management UI
|   |   |   `-- AgentDashboard/  # Agent live-chat dashboard
|   |   |-- config.js            # Frontend API URL and env config
|   |   |-- App.jsx              # Route-based app entry point
|   |   `-- main.jsx             # React DOM entry
|   |-- index.html
|   |-- vite.config.js
|   `-- package.json
|
|-- .github/
|   `-- workflows/
|       `-- keep_alive.yml       # GitHub Actions keep-alive cron job
|
|-- Dockerfile                   # Multi-stage Docker build
|-- .dockerignore
`-- README.md
```

---

## Tech Stack

| Layer                  | Technology                                            |
| ---------------------- | ----------------------------------------------------- |
| **LLM**                | Groq API (fast inference)                             |
| **Embeddings**         | Hugging Face `all-MiniLM-L6-v2`                       |
| **Vector Store**       | ChromaDB                                              |
| **Backend Framework**  | FastAPI + Uvicorn                                     |
| **Real-time**          | Socket.IO (python-socketio)                           |
| **Database**           | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy async |
| **Auth**               | JWT (python-jose), bcrypt, Google OAuth 2.0           |
| **Web Search**         | DuckDuckGo (`ddgs`)                                   |
| **Frontend Framework** | React 19 + Vite 8                                     |
| **HTTP Client**        | Axios                                                 |
| **Real-time Client**   | socket.io-client                                      |
| **Auth Client**        | @react-oauth/google                                   |
| **Analytics**          | @vercel/analytics                                     |
| **Containerization**   | Docker (multi-stage build)                            |
| **CI/CD**              | GitHub Actions                                        |

---

## Getting Started

### Prerequisites

- **Python** 3.11+
- **Node.js** 20+ and npm
- **Groq API Key** — get one free at [console.groq.com](https://console.groq.com)
- **Google OAuth Client ID** (optional, for Google Sign-In) — set up at [Google Cloud Console](https://console.cloud.google.com)
- **Hugging Face Token** (optional, for RAG) — free at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

---

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd MoneyCommandAI/backend

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file (see Environment Variables section)
# Copy and edit the example below
```

---

### Frontend Setup

```bash
# Navigate to the frontend directory
cd MoneyCommandAI/frontend

# Install dependencies
npm install
```

Create a `.env` file in the `frontend/` directory:

```env
# Leave VITE_API_URL blank in local dev — Vite proxy forwards to backend automatically
VITE_API_URL=
VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id
VITE_PERSIST_SESSION=false
```

---

### Running Locally

**Terminal 1 — Backend:**

```bash
cd backend
uvicorn main:socket_app --host 0.0.0.0 --port 8002 --reload
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

The frontend dev server (default: `http://localhost:5173`) proxies API requests to the backend at `http://localhost:8002`.

> **Admin Panel:** `http://localhost:5173/admin`
> **Agent Dashboard:** `http://localhost:5173/agent`

---

## Environment Variables

### Backend (`backend/.env`)

| Variable              | Required    | Description                                                                            |
| --------------------- | ----------- | -------------------------------------------------------------------------------------- |
| `JWT_SECRET_KEY`      | ✅ Required | Strong random secret for JWT signing. **Must be changed in production.**               |
| `GROQ_API_KEY`        | ✅ Required | Your Groq API key for LLM inference.                                                   |
| `CORS_ORIGINS`        | ✅ Required | Comma-separated list of allowed origins. Use `*` for dev, explicit domain(s) for prod. |
| `PORT`                | ✅ Required | Port to run the backend server on (default: `8002`).                                   |
| `DATABASE_URL`        | ⚠️ Prod     | PostgreSQL connection URL for production. Leave blank to use local SQLite.             |
| `GOOGLE_CLIENT_ID`    | ⚠️ Optional | Google OAuth 2.0 client ID (required for Google Sign-In).                              |
| `ADMIN_EMAIL`         | ⚠️ Optional | Email for the default admin account seeded on first run.                               |
| `ADMIN_PASSWORD`      | ⚠️ Optional | Password for the default admin account. **Change before deploying.**                   |
| `AGENT_ADMIN_SECRET`  | ⚠️ Optional | Secret token used to authorize agent account creation.                                 |
| `ENABLE_LIVE_SUPPORT` | ❌ Optional | `true` / `false` — Enable live human support feature (default: `true`).                |
| `ENABLE_RAG`          | ❌ Optional | `true` / `false` — Enable ChromaDB-based RAG retrieval (default: `false`).             |
| `HF_TOKEN`            | ❌ Optional | Hugging Face API token for embeddings (required only if `ENABLE_RAG=true`).            |

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

### Frontend (`frontend/.env`)

| Variable                | Required    | Description                                                                                      |
| ----------------------- | ----------- | ------------------------------------------------------------------------------------------------ |
| `VITE_API_URL`          | ❌ Optional | Absolute backend URL for production (e.g., `https://api.yourapp.com`). Leave empty in local dev. |
| `VITE_GOOGLE_CLIENT_ID` | ⚠️ Optional | Google OAuth 2.0 client ID (same as backend).                                                    |
| `VITE_PERSIST_SESSION`  | ❌ Optional | `true` / `false` — Persist chat session across page reloads (default: `false`).                  |

---

## API Reference

All endpoints are served by the FastAPI backend.

### Chat

| Method | Endpoint | Auth | Description                                                                                  |
| ------ | -------- | ---- | -------------------------------------------------------------------------------------------- |
| `POST` | `/chat`  | None | Send a message; returns an SSE stream of tokens, suggestions, citations, and a `done` event. |

**Request body:**

```json
{
  "message": "How do I log an expense via Telegram?",
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi! How can I help?" }
  ],
  "local_time": "10:30 AM",
  "local_day": "Monday",
  "local_date": "August 18, 2026",
  "session_id": "uuid-v4-string",
  "user_id": 42
}
```

**SSE event types:**

| Event type    | Description                                           |
| ------------- | ----------------------------------------------------- |
| `token`       | A single character or word of the streaming response. |
| `suggestions` | Array of follow-up question suggestions.              |
| `citations`   | Web search source URLs (if web search was triggered). |
| `done`        | Signals the end of the stream.                        |

---

### Health and Status

| Method | Endpoint      | Description                                                     |
| ------ | ------------- | --------------------------------------------------------------- |
| `GET`  | `/health`     | Liveness check: `{"status": "ok"}`                              |
| `HEAD` | `/health`     | Same as above, no body.                                         |
| `GET`  | `/api/status` | Service info and version.                                       |
| `GET`  | `/api/config` | Current feature flags (RAG, live support, session persistence). |

---

### Authentication

| Method | Endpoint            | Description                                           |
| ------ | ------------------- | ----------------------------------------------------- |
| `POST` | `/auth/phone-login` | User login via phone number (rate limited: 5/10 min). |
| `POST` | `/auth/google`      | User login via Google OAuth token.                    |
| `POST` | `/agent/login`      | Support agent login (rate limited: 5/10 min).         |
| `POST` | `/admin/login`      | Admin login (rate limited: 5/10 min).                 |

---

### Live Support

| Method | Endpoint                 | Auth     | Description                                             |
| ------ | ------------------------ | -------- | ------------------------------------------------------- |
| `POST` | `/api/end-session`       | User JWT | End a live support session (used on page unload).       |
| `POST` | `/api/live/cancel-queue` | User JWT | Cancel a waiting queue entry (called via `sendBeacon`). |

---

### Admin APIs

| Method   | Endpoint             | Auth      | Description                             |
| -------- | -------------------- | --------- | --------------------------------------- |
| `GET`    | `/admin/agents`      | Admin JWT | List all support agents.                |
| `POST`   | `/admin/agents`      | Admin JWT | Create a new support agent.             |
| `DELETE` | `/admin/agents/{id}` | Admin JWT | Delete a support agent.                 |
| `GET`    | `/admin/config`      | Admin JWT | Get all dynamic configuration settings. |
| `POST`   | `/admin/config`      | Admin JWT | Update a configuration setting.         |
| `GET`    | `/admin/users`       | Admin JWT | List all registered users.              |

---

## Embeddable Widget

The `widget.js` file in `frontend/public/` lets you embed the chatbot on any website with a single line:

```html
<script src="https://your-deployed-domain.com/widget.js" async></script>
```

**How it works:**

- Injects a fixed-position `<iframe>` that loads the full chatbot UI.
- **Responsive breakpoints:** fullscreen on mobile (≤480px), 480px overlay on tablet (≤768px), floating window on desktop.
- Automatically detects the backend host from the script `src` attribute — no manual config needed.
- **Single-instance guard** prevents duplicate iframes (safe for React strict-mode double-mounts).
- Communicates with the parent page via `window.postMessage` (e.g., for open/close state).

---

## Admin Panel

Accessible at `/admin` (e.g., `http://localhost:5173/admin`).

**Capabilities:**

- Login with admin credentials (seeded automatically on first run).
- **Manage Agents** — Add or remove live support agent accounts.
- **Manage Users** — View all registered users.
- **App Settings** — Toggle RAG, live support, and session persistence on the fly. Changes apply without a server restart.

**Default admin credentials** (change immediately after first login):

| Field    | Default Value                                             |
| -------- | --------------------------------------------------------- |
| Email    | `superadmin@moneycommandai.in` (or `ADMIN_EMAIL` env var) |
| Password | `admin123` (or `ADMIN_PASSWORD` env var)                  |

---

## Agent Dashboard

Accessible at `/agent` (e.g., `http://localhost:5173/agent`).

**Capabilities:**

- Log in with agent credentials created by the admin.
- View the live waiting queue in real time.
- Claim incoming user sessions and engage in real-time chat.
- Mark sessions as resolved.
- View past resolved chat history.

---

## Live Support System

The live support flow uses **Socket.IO** for real-time bidirectional communication:

1. User clicks "Talk to a Human" in the chat widget and joins the waiting queue.
2. Server broadcasts the updated queue to all connected agents.
3. Agent claims the session from their dashboard.
4. Real-time chat begins between user and agent.
5. Either party can end the session; the server updates the database and notifies both sides.

**Stale session cleanup:** On server restart, all "waiting" sessions in the database are automatically resolved to prevent ghost queue entries.

**Reliable unload cleanup:** When a user navigates away while waiting, `navigator.sendBeacon` calls `/api/live/cancel-queue` — unlike `socket.emit`, sendBeacon is guaranteed to fire before the page closes.

---

## RAG (Retrieval-Augmented Generation)

The optional RAG system augments LLM responses with relevant knowledge from a pre-indexed document store.

### Enabling RAG

1. Set `ENABLE_RAG=true` in `backend/.env`.
2. Set `HF_TOKEN` to your Hugging Face API token.
3. Run the ingestion pipeline to populate ChromaDB:

```bash
cd backend
python -m rag.ingest
```

4. Start the server — the chatbot will now retrieve and inject relevant context for each query.

### How It Works

| Step                | Details                                                                                  |
| ------------------- | ---------------------------------------------------------------------------------------- |
| **Embedding model** | `sentence-transformers/all-MiniLM-L6-v2` via Hugging Face Inference API (384 dimensions) |
| **Vector store**    | Local ChromaDB instance stored at `backend/chroma_db/`                                   |
| **Retrieval**       | Top-k most semantically similar document chunks are fetched per query                    |
| **Injection**       | Retrieved chunks are appended to the system prompt as `## Retrieved Help Details`        |
| **Fallback**        | If RAG is disabled or unavailable, the chatbot falls back gracefully to prompt-only mode |

---

## Docker Deployment

The project includes a **multi-stage Dockerfile** that builds the React frontend and packages it alongside the Python backend into a single, self-contained container.

```bash
# Build the Docker image from the project root
docker build -t moneycommandai .

# Run the container
docker run -d \
  -p 8002:8002 \
  --env-file backend/.env \
  --name moneycommandai \
  moneycommandai
```

The application will be available at `http://localhost:8002`.

### What the Dockerfile Does

| Stage              | Base Image         | Action                                                                            |
| ------------------ | ------------------ | --------------------------------------------------------------------------------- |
| `frontend-builder` | `node:20-alpine`   | Installs npm dependencies and runs `npm run build`                                |
| `backend`          | `python:3.11-slim` | Installs Python deps, copies backend source, copies frontend `dist/` from Stage 1 |

The FastAPI app serves the static frontend and falls back to `index.html` for client-side routing. A Docker health check pings `/api/status` every 30 seconds.

---

## CI/CD — Keep Alive Workflow

For deployments on free-tier platforms (e.g., Railway, Render) that spin down idle services, a GitHub Actions workflow keeps the backend warm.

**File:** `.github/workflows/keep_alive.yml`

**Schedule:** Runs every 10 minutes between 08:00 AM and 02:00 AM IST (02:30 – 20:30 UTC).

**What it does:** Runs `backend/keep_alive.py`, which makes HTTP GET requests to the health endpoint to prevent the service from going cold.

You can also trigger it manually from the GitHub Actions UI via `workflow_dispatch`.

---

## Security

| Area                   | Implementation                                                                            |
| ---------------------- | ----------------------------------------------------------------------------------------- |
| **JWT Signing**        | `JWT_SECRET_KEY` env var required; server exits at startup if unset or using the default. |
| **Password Hashing**   | `bcrypt` via `passlib[bcrypt]`. Plain-text passwords are never stored.                    |
| **CORS**               | Driven by `CORS_ORIGINS` env var; wildcard (`*`) automatically disables `credentials`.    |
| **Rate Limiting**      | Per-IP sliding window: 30 req/60 s for chat, 5 attempts/10 min for auth endpoints.        |
| **Content Safety**     | Vulgar and negative content filters run on every message before LLM invocation.           |
| **Agent Registration** | `AGENT_ADMIN_SECRET` env var required to register new agent accounts.                     |
| **Secrets Management** | `.env` is gitignored. All secrets are loaded from environment variables only.             |

> ⚠️ **Important:** The example `.env` values in this repo are for local development only. **Rotate all secrets before deploying to production.**

---

## Contributing

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/your-feature-name
```

3. Make your changes with clear, descriptive commit messages.
4. Run the backend tests:

```bash
cd backend
pytest
```

5. Open a Pull Request describing what you changed and why.

---

## License

This project is proprietary software. All rights reserved.

---

<div align="center">

  <img src="https://raw.githubusercontent.com/kabilannadar/MoneyCommandAI-Assistant/main/frontend/public/chatbot_mascot.png" alt="MoneyCommandAI Mascot" width="120" />

  <h3>MoneyCommandAI Assistant</h3>

  <p>Powered by <a href="https://expensetrackertn.vercel.app"><strong>ExpenseTracker</strong></a></p>

  <p>
    <a href="https://expensetrackertn.vercel.app">🌐 Live App</a>
    &nbsp;•&nbsp;
    <a href="https://expensetrackertn.vercel.app/support">💬 Support & Feedback</a>
    &nbsp;•&nbsp;
    <a href="https://t.me/expensetrackertnbot">🤖 Telegram Bot</a>
    &nbsp;•&nbsp;
    <a href="mailto:r.r.kabilan0335@gmail.com">✉️ Email Us</a>
  </p>

<sub>© 2026 MoneyCommandAI. All rights reserved.</sub>

</div>
