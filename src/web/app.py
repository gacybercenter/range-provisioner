"""
FastAPI application factory for Range Provisioner.
"""
import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

try:
    from src.web.routes.api import router as api_router
    from src.web.routes.auth_admin import router as auth_router
    from src.web.routes.live_monitor import router as live_monitor_router
    from src.web.routes.scheduler import router as scheduler_router, run_scheduler_background_task
    from src.db import init_db
except ImportError:
    from web.routes.api import router as api_router
    from web.routes.auth_admin import router as auth_router
    from web.routes.live_monitor import router as live_monitor_router
    from web.routes.scheduler import router as scheduler_router, run_scheduler_background_task
    from db import init_db

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure SQLite tables exist and default admin is seeded
    try:
        init_db()
    except Exception as exc:
        print(f"Warning: Database initialization notice: {exc}")

    scheduler_task = asyncio.create_task(run_scheduler_background_task())
    try:
        yield
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Range Provisioner Studio & API",
    description="Cyber Range Orchestration Platform for OpenStack Heat, Swift, and Apache Guacamole.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(auth_router)
app.include_router(live_monitor_router)
app.include_router(scheduler_router)

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Range Provisioner Studio</h1><p>index.html template not found.</p>", status_code=404)
    content = index_file.read_text(encoding="utf-8")
    return HTMLResponse(content)

