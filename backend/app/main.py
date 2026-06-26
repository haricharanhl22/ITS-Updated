# Monkeypatch httpx to disable HTTP/2 on Windows (fixes WinError 10035 socket issues)
import httpx
_orig_init = httpx.Client.__init__
def _patched_init(self, *args, **kwargs):
    kwargs["http2"] = False
    _orig_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_init

_orig_async_init = httpx.AsyncClient.__init__
def _patched_async_init(self, *args, **kwargs):
    kwargs["http2"] = False
    _orig_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched_async_init

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth            import router as auth_router
from app.api.chat            import router as chat_router
from app.api.mastery         import router as mastery_router
from app.api.assessments     import router as assessments_router
from app.api.ask             import router as ask_router
from app.api.demo            import router as demo_router
from app.api.learning_events import router as learning_events_router
from app.api.admin           import router as admin_router
from app.config.settings     import settings

app = FastAPI(
    title=settings.app_name,
    description="HCAI-ITS — Intelligent Tutoring System API",
    version="2.0.0",
)

# Allow both Vite dev server ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(mastery_router)
app.include_router(assessments_router)
app.include_router(ask_router)
app.include_router(demo_router)
app.include_router(learning_events_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}
