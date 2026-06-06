import time
import logging
import uuid
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

logger = logging.getLogger(__name__)

class RequestIDMiddleware:
    """Middleware to attach or generate a request id and measure request time.

    Sets `request.state.request_id` and adds it to log records via structured logging helper.
    """
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-Id"):
        self.app = app
        self.header_name = header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        scope.setdefault("extensions", {})["request_id"] = request_id
        scope.setdefault("state", type("S", (), {})())
        scope["state"] = getattr(scope, "state")
        scope["state"].request_id = request_id

        start = time.time()
        async def send_wrapper(message):
            await send(message)
        await self.app(scope, receive, send_wrapper)
        duration = time.time() - start
        logger.info("request.completed", extra={"request_id": request_id, "path": scope.get("path"), "method": scope.get("method"), "duration": duration})
