"""
PIXELNOVA Backend - FastAPI entrypoint

Run locally with:
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as scenes_router

app = FastAPI(
    title="PIXELNOVA API",
    description="AI-Based Uncertainty-Aware Super-Resolution of Sentinel-2 Imagery",
    version="0.1.0-phase1",
)

# Local dev origins always allowed. In production, set FRONTEND_URL to the
# deployed static site's URL (Render sets this via env var, see render.yaml).
default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
frontend_url = os.environ.get("FRONTEND_URL")
allow_origins = default_origins + ([frontend_url] if frontend_url else [])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scenes_router, prefix="/api", tags=["scenes"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "phase": "1 - upload/validate/preview"}
