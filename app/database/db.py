"""
Database engine, session factory, and init function for MySQL.
Uses SQLAlchemy + PyMySQL driver.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.utils.logger import get_logger

load_dotenv(Path(__file__).parent.parent.parent / ".env")

logger = get_logger(__name__)

# ── Connection settings from .env ─────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "document_extractor")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

logger.info("Database URL configured for host=%s db=%s", DB_HOST, DB_NAME)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # verify connections before use
    pool_recycle=3600,           # recycle connections every hour
    echo=False,                  # set True for SQL debug logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist. Called on app startup."""
    from app.database import models  # noqa: F401 – registers models with Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialised (MySQL: %s/%s)", DB_HOST, DB_NAME)
    except Exception as exc:
        logger.error("Failed to initialise database: %s", exc)
        raise