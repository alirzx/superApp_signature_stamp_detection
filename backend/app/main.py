"""SuperApp Module 06: CPU-only stamp and signature localization API."""
import asyncio
import hmac
import logging
from contextlib import asynccontextmanager
from typing import Callable
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from app.core.config import Settings
from app.inference.rfdetr import RFDETREngine
from app.services.detection import DetectionService
from app.preprocessing.images import InvalidImage

logger = logging.getLogger(__name__)
REQUESTS = Counter("superapp_mark_requests_total", "Stamp/signature requests", ["route", "status"])
LATENCY = Histogram("superapp_mark_request_seconds", "Stamp/signature processing seconds", ["route"])


def create_app(settings: Settings | None = None, engine_factory: Callable = RFDETREngine) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = engine_factory(settings)
        await run_in_threadpool(engine.initialize)
        app.state.engine = engine
        app.state.service = DetectionService(engine, settings)
        app.state.semaphore = asyncio.Semaphore(settings.max_concurrent_inference)
        yield

    app = FastAPI(title="SuperApp Signature & Stamp Detection", version="0.1.0", lifespan=lifespan,
                  docs_url=None if settings.app_env == "production" else "/docs", redoc_url=None)

    @app.middleware("http")
    async def headers(request: Request, call_next):
        if request.method == "POST" and request.url.path.startswith("/v1/"):
            value = request.headers.get("content-length")
            if value is not None:
                try:
                    if int(value) > settings.max_request_bytes:
                        return JSONResponse({"detail": "Request body too large"}, status_code=413)
                except ValueError:
                    return JSONResponse({"detail": "Invalid content length"}, status_code=400)
        result = await call_next(request)
        result.headers["X-Content-Type-Options"] = "nosniff"
        result.headers["Cache-Control"] = "no-store"
        return result

    def authorize(x_api_key: str | None = Header(default=None)):
        if settings.api_token and not hmac.compare_digest(x_api_key or "", settings.api_token):
            raise HTTPException(401, detail="Invalid API key")

    @app.get("/health/live")
    async def live():
        return {"status": "alive"}

    @app.get("/health/ready")
    async def ready():
        if not getattr(getattr(app.state, "engine", None), "ready", False):
            return JSONResponse({"status": "not_ready"}, status_code=503)
        return {"status": "ready", "backend": "rfdetr", "device": "cpu"}

    @app.get("/v1/models", dependencies=[Depends(authorize)])
    async def models():
        return {"models": [{"id": settings.model_repo, "revision": settings.model_revision,
                 "device": "cpu", "backend": "rfdetr", "ready": bool(app.state.engine.ready),
                 "classes": ["stamp", "signature"], "score_threshold": settings.score_threshold}]}

    @app.get("/metrics", dependencies=[Depends(authorize)])
    async def metrics():
        if not settings.enable_metrics:
            raise HTTPException(404)
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    async def process(file: UploadFile, document_id: str, page_id: str, page_number: int,
                      threshold: float | None, kind: str | None):
        route = kind or "both"
        if len(document_id) > 128 or len(page_id) > 128 or not document_id.strip() or not page_id.strip():
            raise HTTPException(422, "Invalid document/page ID")
        if page_number < 1 or page_number > 10000:
            raise HTTPException(422, "Invalid page_number")
        value = settings.score_threshold if threshold is None else threshold
        if not 0.01 <= value <= 0.99:
            raise HTTPException(422, "threshold must be in [0.01,0.99]")
        max_bytes = settings.max_upload_mb * 1024 * 1024
        data = await file.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise HTTPException(413, "Image too large")
        try:
            await asyncio.wait_for(app.state.semaphore.acquire(), timeout=settings.max_queue_wait_seconds)
        except asyncio.TimeoutError as exc:
            REQUESTS.labels(route, "busy").inc()
            raise HTTPException(503, "Inference capacity exceeded", headers={"Retry-After": "3"}) from exc
        import time
        start = time.perf_counter()
        try:
            result = await run_in_threadpool(app.state.service.process, data, (file.filename or "image")[:160],
                                             document_id, page_id, page_number, value, kind)
            REQUESTS.labels(route, "ok").inc()
            return result
        except InvalidImage as exc:
            REQUESTS.labels(route, "invalid").inc()
            raise HTTPException(422, str(exc)) from exc
        except Exception:
            REQUESTS.labels(route, "error").inc()
            logger.exception("Stamp/signature inference failed")
            raise HTTPException(500, "Inference failed; see server diagnostics")
        finally:
            LATENCY.labels(route).observe(time.perf_counter() - start)
            app.state.semaphore.release()
            await file.close()

    @app.post("/v1/detect", dependencies=[Depends(authorize)])
    async def detect(file: UploadFile = File(...), document_id: str = Form("upload"),
                     page_id: str = Form("page-1"), page_number: int = Form(1),
                     threshold: float | None = Form(default=None)):
        return await process(file, document_id, page_id, page_number, threshold, None)

    @app.post("/v1/detect/stamps", dependencies=[Depends(authorize)])
    async def detect_stamps(file: UploadFile = File(...), document_id: str = Form("upload"),
                     page_id: str = Form("page-1"), page_number: int = Form(1),
                     threshold: float | None = Form(default=None)):
        return await process(file, document_id, page_id, page_number, threshold, "stamp")

    @app.post("/v1/detect/signatures", dependencies=[Depends(authorize)])
    async def detect_signatures(file: UploadFile = File(...), document_id: str = Form("upload"),
                     page_id: str = Form("page-1"), page_number: int = Form(1),
                     threshold: float | None = Form(default=None)):
        return await process(file, document_id, page_id, page_number, threshold, "signature")

    return app


app = create_app()
