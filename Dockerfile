# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Build React frontend
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies first (cached layer if package.json unchanged)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent

# Copy source and build
COPY frontend/ ./
RUN npm run build


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Python backend + bundled frontend dist
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS backend

# System dependencies for chromadb / torch / bcrypt native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend dist from stage 1 into expected location
# main.py looks for: <repo_root>/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set working directory to backend so relative imports resolve correctly
WORKDIR /app/backend

# Expose the application port
EXPOSE 8002

# Health check — Docker will mark container as unhealthy if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8002/api/status || exit 1

# Run the Socket.IO-wrapped ASGI app via uvicorn.
# main:socket_app is the correct entrypoint — it wraps FastAPI with Socket.IO.
CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
