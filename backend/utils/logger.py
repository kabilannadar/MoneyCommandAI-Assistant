import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# ── 1. Resolve logs directory ────────────────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BACKEND_DIR, "logs")

try:
    os.makedirs(LOGS_DIR, exist_ok=True)
except Exception as e:
    print(f"[LOGGER ERROR] Failed to create logs directory: {e}", file=sys.stderr)


# ── 2. Custom level filter ───────────────────────────────────────────────────
class MinLevelFilter(logging.Filter):
    """Allow only records at or above min_level but strictly below max_level."""
    def __init__(self, min_level: int, max_level: int = logging.CRITICAL + 1):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return self.min_level <= record.levelno < self.max_level


# ── 3. Root logger ───────────────────────────────────────────────────────────
logger = logging.getLogger("moneycommandai_chatbot")
logger.setLevel(logging.INFO)   # ignore DEBUG logs

# Prevent duplicate handlers if module is re-imported (e.g. uvicorn --reload)
if not logger.handlers:

    # Shared formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ── 4a. stdout stream handler — required for container log collection ───
    # Docker, Railway, Render, GCP Cloud Run, AWS ECS all read from stdout/stderr.
    # Without this, logs written only to rotating files are lost on container restart.
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


    # ── 4a. info.log — INFO only ────────────────────────────────────────────
    # Captures: server start, connections, logins, Groq timing, cache, RAG state
    _info_path = os.path.join(LOGS_DIR, "info.log")
    try:
        info_handler = RotatingFileHandler(
            _info_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        info_handler.setLevel(logging.INFO)
        info_handler.addFilter(MinLevelFilter(logging.INFO, logging.WARNING))
        info_handler.setFormatter(formatter)
        logger.addHandler(info_handler)
    except Exception as e:
        print(f"[LOGGER ERROR] Failed to initialise info.log: {e}", file=sys.stderr)

    # ── 4b. warning.log — WARNING only ──────────────────────────────────────
    # Captures: rate limits, auth failures, security alerts, 404s
    _warn_path = os.path.join(LOGS_DIR, "warning.log")
    try:
        warn_handler = RotatingFileHandler(
            _warn_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        warn_handler.setLevel(logging.WARNING)
        warn_handler.addFilter(MinLevelFilter(logging.WARNING, logging.ERROR))
        warn_handler.setFormatter(formatter)
        logger.addHandler(warn_handler)
    except Exception as e:
        print(f"[LOGGER ERROR] Failed to initialise warning.log: {e}", file=sys.stderr)

    # ── 4c. error.log — ERROR only ──────────────────────────────────────────
    # Captures: API failures, DB errors, unhandled exceptions
    _error_path = os.path.join(LOGS_DIR, "error.log")
    try:
        error_handler = RotatingFileHandler(
            _error_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(MinLevelFilter(logging.ERROR, logging.CRITICAL))
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    except Exception as e:
        print(f"[LOGGER ERROR] Failed to initialise error.log: {e}", file=sys.stderr)

