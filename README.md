<p align="center">
  <img src="https://raw.githubusercontent.com/kabilannadar/MoneyCommandAI-Assistant/main/frontend/public/MoneyCommandAI_Chatbot_Banner.png" alt="MoneyCommandAI Assistant Banner" width="100%" />
</p>

<h3 align="center">MoneyCommandAI Assistant</h3>
<p align="center">
  <strong>The smart AI support layer embedded inside <a href="https://expensetrackertn.vercel.app">ExpenseTracker</a> — helping users master their personal finances via natural language chat.</strong>
</p>

<p align="center">
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
</p>

<p align="center">
  <a href="https://expensetrackertn.vercel.app" target="_blank">
    <img src="https://img.shields.io/badge/Live_Website-Visit_ExpenseTracker-b05f30?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Live Website" />
  </a>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Tech Stack](#️-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Running Locally](#running-locally)
- [Environment Variables](#️-environment-variables)
- [API Reference](#-api-reference)
- [Embeddable Widget](#-embeddable-widget)
- [Admin Panel & Agent Dashboard](#️-admin-panel--agent-dashboard)
- [Live Support System](#-live-support-system)
- [RAG (Retrieval-Augmented Generation)](#-rag-retrieval-augmented-generation)
- [Docker Deployment](#-docker-deployment)
- [CI/CD — Keep Alive Workflow](#-cicd--keep-alive-workflow)
- [Security & Content Safety](#-security--content-safety)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact & Connect](#-contact--connect)

---

## 📖 Overview

**MoneyCommandAI Assistant** is a production-grade, full-stack AI chatbot application built to serve as the intelligent support layer for the ExpenseTracker personal finance platform. It helps users understand app features, set up Telegram bot logging, manage budgets/goals/reminders, and escalate to live human agents when needed.

The system is composed of:
- A **FastAPI** backend with streaming SSE responses, Socket.IO real-time communication, JWT authentication, and a SQLite/PostgreSQL database.
- A **React** (Vite) frontend that renders the chat interface, an agent dashboard, and an admin panel.
- An **embeddable JavaScript widget** (`widget.js`) that injects the chatbot into any third-party webpage via a single `<script>` tag.

---

## 🚀 Key Features

- **🤖 AI Chatbot Engine:** Powered by Groq LLM with intent detection (`GREETING`, `TELEGRAM_SETUP`, `TELEGRAM_LOGGING`, `APP_FEATURES`, `SUPPORT_CONTACT`) to inject context, response streaming via Server-Sent Events (SSE), and fallback DuckDuckGo web search.
- **🔍 Retrieval-Augmented Generation (RAG):** Semantic knowledge base querying powered by ChromaDB and Hugging Face embeddings (`all-MiniLM-L6-v2`) with a graceful fallback system.
- **💬 Live Support Escalation:** Real-time user-to-agent WebSocket messaging via Socket.IO, active queue broadcasting, and agent claiming dashboard with automatic stale session cleanup.
- **🔒 Safety & Rate Limiting:** Vulgar/offensive content blocks, negative sentiment detection, JWT auth (Google OAuth 2.0 / Phone), and strict per-IP rate limits for chat and auth endpoints.
- **⚙️ Dynamic Admin controls:** Create/manage agents, configure live flags (RAG, live support, session persistence) dynamically without requiring a server restart.
- **🔌 Embeddable Chat Widget:** Iframe-based drop-in JS widget that is responsive, handles dynamic resizing, and initializes communication via `postMessage`.

---

## 📐 Architecture

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

## 📂 Project Structure

```text
├── backend/                    # FastAPI python backend service
│   ├── auth/                   # Authentication & user/agent management APIs
│   │   ├── auth.py             # User Google OAuth & phone login
│   │   ├── agent_auth.py       # Support agent session auth
│   │   ├── admin_auth.py       # Admin credential validation
│   │   ├── admin_agents.py     # Live-chat agent CRUD endpoints
│   │   ├── admin_config.py     # Dynamic system settings control
│   │   └── admin_users.py      # Customer profile query APIs
│   ├── chatbot/                # Core AI orchestrator
│   │   ├── chatbot.py          # Response generation & SSE streaming
│   │   ├── intent.py           # NLP intent classifiers
│   │   ├── prompts.py          # System prompt builders
│   │   ├── prompt_blocks.py    # Modular prompt components
│   │   ├── data.py             # Static fallback query info
│   │   ├── cache.py            # In-memory query-response caching
│   │   ├── security.py         # Vulgarity & mood filters
│   │   ├── responses.py        # Preset system responses
│   │   └── web_search.py       # Scoped DuckDuckGo fallback search
│   ├── db/                     # Data persistence layer
│   │   ├── database.py         # SQLAlchemy engine & async session builder
│   │   └── models.py           # ORM schemas (Users, Agents, Sessions)
│   ├── live/                   # Human escalation support layer
│   │   ├── live_chat.py        # Socket.IO bidirectional event handlers
│   │   ├── sio_instance.py     # Shared WebSocket server instance
│   │   └── state.py            # In-memory queue & claimed state management
│   ├── rag/                    # Retrieval-Augmented Generation
│   │   ├── rag.py              # ChromaDB vector retrieval logic
│   │   └── ingest.py           # Knowledgebase ingestion script
│   ├── utils/                  # System-wide helpers
│   │   └── logger.py           # Structured debug logger
│   ├── config.py               # Env var parsing & client initiations
│   ├── keep_alive.py           # Free-tier server sleep preventer
│   ├── main.py                 # FastAPI application root & middleware setup
│   └── requirements.txt        # Python dependency manifest
├── frontend/                   # React web application
│   ├── public/
│   │   ├── widget.js           # Independent drop-in iframe widget
│   │   └── chatbot_mascot.png  # Asset: chatbot avatar mascot
│   ├── src/
│   │   ├── components/         # Reusable UI widgets
│   │   │   ├── Chatbot/        # Floating chatbot bubble & dialogue frame
│   │   │   ├── LiveChatPanel/  # Agent interface socket chat interface
│   │   │   └── UserInfoModal/  # User profiling popup modal
│   │   ├── pages/              # Routed pages
│   │   │   ├── AdminPanel/     # Dynamic controls & agent creation dashboard
│   │   │   └── AgentDashboard/ # Support ticket claiming and routing queue
│   │   ├── config.js           # API route mapper & frontend client state
│   │   ├── App.jsx             # Main react-router routing shell
│   │   └── main.jsx            # Application render entrypoint
│   ├── index.html              # HTML DOM anchor point
│   ├── vite.config.js          # Vite bundler rules & api proxy setup
│   └── package.json            # Node modules registry
├── .github/workflows/
│   └── keep_alive.yml          # Cron action to wake backend
├── Dockerfile                  # Multi-stage production container instructions
├── .dockerignore
└── README.md                   # This project index page
```

---

## 🛠️ Tech Stack

- **LLM Engine:** Groq API (Fast Inference)
- **Vector Database:** ChromaDB with Hugging Face `all-MiniLM-L6-v2` embeddings
- **Backend Framework:** FastAPI (Uvicorn, SQLAlchemy async)
- **Real-time Communication:** Socket.IO (`python-socketio` & `socket.io-client`)
- **Frontend Client:** React 19, Vite 8 (using Axios & `@react-oauth/google`)
- **Containerization & CI/CD:** Docker (multi-stage build) & GitHub Actions

### Detailed Tech Stack

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

## 💻 Getting Started

### Prerequisites

- **Python** 3.11+
- **Node.js** 20+ and npm
- **Groq API Key** — get one free at [console.groq.com](https://console.groq.com)
- **Google OAuth Client ID** (optional, for Google Sign-In) — set up at [Google Cloud Console](https://console.cloud.google.com)
- **Hugging Face Token** (optional, for RAG) — free at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

---

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```
2. **Create and activate a virtual environment:**
   - **Windows:**
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Create your `.env` file:** Copy and edit the environment variables in a new `.env` file within the `backend/` directory.

---

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```
2. **Install dependencies:**
   ```bash
   npm install
   ```
3. **Create a `.env` file in the `frontend/` directory:**
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

## ⚙️ Environment Variables

### Backend Settings (`backend/.env`)

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

> [!WARNING]
> **Never commit your `.env` file.** It is already listed in `.gitignore`.

### Frontend Settings (`frontend/.env`)

| Variable                | Required    | Description                                                                                      |
| ----------------------- | ----------- | ------------------------------------------------------------------------------------------------ |
| `VITE_API_URL`          | ❌ Optional | Absolute backend URL for production (e.g., `https://api.yourapp.com`). Leave empty in local dev. |
| `VITE_GOOGLE_CLIENT_ID` | ⚠️ Optional | Google OAuth 2.0 client ID (same as backend).                                                    |
| `VITE_PERSIST_SESSION`  | ❌ Optional | `true` / `false` — Persist chat session across page reloads (default: `false`).                  |

---

## 📖 API Reference

### Chat Endpoints

| Method | Endpoint | Auth | Description                                                                                  |
| ------ | -------- | ---- | -------------------------------------------------------------------------------------------- |
| `POST` | `/chat`  | None | Send a message; returns an SSE stream of tokens, suggestions, citations, and a `done` event. |

**Request Body Example:**
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

**SSE Event Types:**

| Event Type    | Description                                           |
| ------------- | ----------------------------------------------------- |
| `token`       | A single character or word of the streaming response. |
| `suggestions` | Array of follow-up question suggestions.              |
| `citations`   | Web search source URLs (if web search was triggered). |
| `done`        | Signals the end of the stream.                        |

---

### Health & Status

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

## 🔌 Embeddable Widget

The `widget.js` file in `frontend/public/` lets you embed the chatbot on any website with a single line:

```html
<script src="https://your-deployed-domain.com/widget.js" async></script>
```

- **Dynamic Frame:** Injects a fixed-position `<iframe>` loading the chatbot UI.
- **Breakpoints:** Responsive fullscreen layout on mobile (≤480px) and a standard overlay on tablet/desktop.
- **Auto-Host Resolution:** Auto-detects the backend endpoint from the script `src` attribute.
- **Communication:** Sends message events using the `postMessage` protocol.

---

## 🖥️ Admin Panel & Agent Dashboard

### Admin Panel (`/admin`)
- Control Agent profiles (Create, Read, Delete).
- Monitor all registered users.
- Modify active configuration keys (RAG, live support, session persistence flags) on the fly without rebooting the backend service.

**Default Credentials:**
| Field    | Default Value                                             |
| -------- | --------------------------------------------------------- |
| Email    | `superadmin@moneycommandai.in` (or `ADMIN_EMAIL` env var) |
| Password | `admin123` (or `ADMIN_PASSWORD` env var)                  |

### Agent Dashboard (`/agent`)
- Live queue parsing and visual ticket list.
- Real-time Socket.IO chat windows for claimed sessions.
- Status updating (resolve, escalate) and past interaction archive views.

---

## 💬 Live Support System

1. **Ticket Request:** User clicks "Talk to a Human" and triggers queue entry.
2. **Event Broadcast:** Server notifies all connected support agent sessions.
3. **Claim Ticket:** An agent clicks claim to open a dedicated WebSocket lane.
4. **Chat Session:** Real-time messages are shared using Socket.IO.
5. **Garbage Cleanup:** If a user unloads the page before connection, `navigator.sendBeacon` triggers queue cancellation. Stale sessions automatically clear on system reboot.

---

## 🔍 RAG Ingestion & Vector DB

To enable ChromaDB document context retrieval:
1. Set `ENABLE_RAG=true` and your Hugging Face API key in `backend/.env`.
2. Seed the Chroma vector store by running the ingestion engine:
   ```bash
   cd backend
   python -m rag.ingest
   ```
3. Restart the backend service.

### Pipeline Details

| Stage               | Details                                                                                  |
| ------------------- | ---------------------------------------------------------------------------------------- |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` via Hugging Face Inference API (384 dimensions) |
| **Vector Store**    | Local ChromaDB instance stored at `backend/chroma_db/`                                   |
| **Retrieval Query** | Fetches top-k similar document chunks per user text prompt                               |
| **System Injection**| Prepends context into system prompts as `## Retrieved Help Details`                      |

---

## 🐳 Docker Deployment

The multi-stage `Dockerfile` packages the React assets and FastAPI server together:

```bash
# Build the Docker image
docker build -t moneycommandai .

# Run the container
docker run -d \
  -p 8002:8002 \
  --env-file backend/.env \
  --name moneycommandai \
  moneycommandai
```

### Docker Stages

- **Stage 1 (Frontend Builder):** Uses `node:20-alpine` to compile assets into `frontend/dist/`.
- **Stage 2 (Backend Production):** Uses `python:3.11-slim` to serve backend routes and static frontend bundles under Uvicorn. Includes a liveness health check target (`/api/status`).

---

## 🔄 CI/CD & Keep-Alive Workflows

Deployments on free tiers (like Render/Railway) may spin down due to inactivity.

- **Keep-Alive Script:** `backend/keep_alive.py` issues routine HTTP pings to the `/health` endpoint.
- **Workflow schedule:** `.github/workflows/keep_alive.yml` fires every 10 minutes between 8:00 AM and 2:00 AM IST.

---

## 🛡️ Security & Content Safety

| Metric                 | Logic Details                                                                              |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| **JWT Verification**   | Enforces strong custom `JWT_SECRET_KEY` env validation; fails instantly if default.       |
| **Data Hashing**       | Hashes passwords with `bcrypt` encryption before committing to DB.                         |
| **CORS Guard**         | Restricts browser domains via `CORS_ORIGINS`; wildcard blocks cross-site cookie usage.     |
| **Rate Limiters**      | Chat triggers limit at 30 req/min; Authorization calls throttle at 5 attempts/10 min.      |
| **Content Screening**  | Rejects vulgar phrases and responds to hostile users using negative sentiment prompts.      |

---

## 🤝 Contributing

1. Fork this project repository.
2. Branch out to your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit with descriptive descriptions and write unit tests where possible.
4. Verify backend functionality:
   ```bash
   cd backend
   pytest
   ```
5. Submit a pull request detailing your improvements.

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 📬 Contact & Connect

- **Live App:** [ExpenseTracker](https://expensetrackertn.vercel.app)
- **Telegram Bot:** [@expensetrackertnbot](https://t.me/expensetrackertnbot)
- **Support & Feedback:** [ExpenseTracker Support](https://expensetrackertn.vercel.app/support)
- **Email:** [r.r.kabilan0335@gmail.com](mailto:r.r.kabilan0335@gmail.com)

---

<p align="center">
  <sub>© 2026 MoneyCommandAI. Powered by ExpenseTracker. All rights reserved.</sub>
</p>
