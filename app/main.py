"""
FastAPI application entry point.
- CORS middleware (open for local dev)
- Lifespan: initialise MySQL tables on startup
- Swagger UI at /docs
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database.db import init_db
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create MySQL tables. Shutdown: nothing special needed."""
    logger.info("Starting Document Extractor API…")
    init_db()
    yield
    logger.info("Shutting down Document Extractor API.")


app = FastAPI(
    title="Intelligent Document Extraction Platform",
    description=(
        "Scan and process uploaded documents (Aadhaar, Driving Licence, "
        "Passport, Invoice) using OCR + LLM-based field extraction.\n\n"
        "**Tech Stack**: FastAPI · Tesseract OCR · OpenAI GPT-3.5 · MySQL"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow all origins for local dev) ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)