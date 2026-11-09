"""ASGI-level HTTP request-body guard ahead of FastAPI's multipart parser.

Body data is bounded in memory before handing it to Starlette. This ensures
chunked requests without Content-Length return 413, not a multipart 400 error.
"""
from fastapi.responses import JSONResponse


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") != "POST" or not scope.get("path", "").startswith("/v1/"):
            await self.app(scope, receive, send)
            return

        for key, value in scope.get("headers", []):
            if key.lower() != b"content-length":
                continue
            try:
                declared = int(value)
                if declared < 0:
                    raise ValueError
            except ValueError:
                await JSONResponse({"detail": "Invalid content length"}, status_code=400)(scope, receive, send)
                return
            if declared > self.max_bytes:
                await JSONResponse({"detail": "Request body too large"}, status_code=413)(scope, receive, send)
                return

        chunks = []
        size = 0
        while True:
            event = await receive()
            if event["type"] != "http.request":
                # Disconnect before the request body was complete.
                return
            chunk = event.get("body", b"")
            size += len(chunk)
            if size > self.max_bytes:
                await JSONResponse({"detail": "Request body too large"}, status_code=413)(scope, receive, send)
                return
            chunks.append(chunk)
            if not event.get("more_body", False):
                break

        # The second-stage application receives one bounded, replayable ASGI body.
        body = b"".join(chunks)
        delivered = False

        async def replay_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        await self.app(scope, replay_receive, send)