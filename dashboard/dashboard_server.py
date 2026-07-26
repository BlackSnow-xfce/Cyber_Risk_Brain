from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.predator_engine import PredatorEngine
from dashboard.dashboard_data import DashboardDataBuilder

app = FastAPI(title="PredatorAI Dashboard")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )

engine = PredatorEngine()
builder = DashboardDataBuilder()


@app.get("/api/dashboard")
def dashboard() -> dict:
    result = engine.run()
    return builder.build(result)


@app.get("/")
def index():
    index_file = STATIC_DIR / "index.html"

    if index_file.exists():
        return FileResponse(index_file)

    return {
        "application": "PredatorAI Dashboard",
        "status": "running",
        "message": "Frontend not installed yet.",
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "engine": "PredatorAI v2",
    }
