import os
import socketio

_raw_cors = os.getenv("CORS_ORIGINS", "*").strip()
_sio_cors = [o.strip() for o in _raw_cors.split(",") if o.strip()]
# Socket.IO accepts "*" string or a list of origins
_sio_cors_value = "*" if "*" in _sio_cors else _sio_cors

sio = socketio.AsyncServer(
    async_mode           = "asgi",
    cors_allowed_origins = _sio_cors_value,
    logger               = False,
    engineio_logger      = False,
)
