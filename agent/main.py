"""
FastAPI application entry-point for AI Project Navigator.
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.rag import index_documents
from agent.routes import blockers, meeting, next_step, requirements
from agent.tasks import router as tasks_router

# ---------------------------------------------------------------------------
# Logging setup (UTF-8 safe on Windows)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: index documents at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== AI Project Navigator starting ===")
    try:
        n = await index_documents()
        logger.info("Startup: indexed %d chunks.", n)
    except Exception as exc:
        logger.warning("Startup indexing failed (will retry on /index): %s", exc)
    yield
    logger.info("=== AI Project Navigator shutting down ===")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Project Navigator",
    description=(
        "AI assistant for PM leading AI integration projects. "
        "Powered by NeuralDeep GPT-OSS-120B + ChromaDB RAG."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow Streamlit (any localhost origin) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(meeting.router)
app.include_router(requirements.router)
app.include_router(blockers.router)
app.include_router(next_step.router)
app.include_router(tasks_router)


# ---------------------------------------------------------------------------
# Utility endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["health"])
async def root() -> dict:
    return {"status": "ok", "service": "AI Project Navigator"}


@app.post("/index", tags=["admin"], summary="Re-index all documents")
async def reindex() -> dict:
    """Force re-indexing of all documents in the data/ directory."""
    n = await index_documents()
    return {"status": "ok", "chunks_indexed": n}
