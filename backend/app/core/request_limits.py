"""ASGI-level HTTP body guard, before FastAPI parses multipart uploads."""
from fastapi.responses import JSONResponse


class RequestBodyTooLarge(Exception):
    pass


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") != "POST" or not scope.get("path", "").startswith("/v1/"):
            await self.app(scope, receive, send)
            return
        for key, value in scope.get("headers", []):
            if key.lower() == b"content-length":
                try:
                    length = int(value)
                    if length < 0:
                        raise ValueError
                except ValueError:
                    await JSONResponse({"detail": "Invalid content length"}, status_code=400)(scope, receive, send)
                    return
                if length > self.max_bytes:
                    await JSONResponse({"detail": "Request body too large"}, status_code=413)(scope, receive, send)
                    return
        received = 0
        started = False

        async def limited_receive():
            nonlocal received
            event = await receive()
            if event["type"] == "http.request":
                received += len(event.get("body", b""))
                if received > self.max_bytes:
                    raise RequestBodyTooLarge
            return event

        async def tracked_send(event):
            nonlocal started
            if event["type"] == "http.response.start":
                started = True
            await send(event)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except RequestBodyTooLarge:
            if not started:
                await JSONResponse({"detail": "Request body too large"}, status_code=413)(scope, receive, send)
            else:
                # No second response may be emitted after headers have started.
                raise