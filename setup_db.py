"""
One-time setup script: creates the MySQL database 'document_extractor'
and all ORM tables. Run once before starting the API.

Usage (from document_extractor/ folder):
    venv\Scripts\python setup_db.py
"""

import os
import sys
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

import pymysql

DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_NAME     = os.getenv("DB_NAME",     "document_extractor")
DB_USER     = os.getenv("DB_USER",     "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def create_database():
    print(f"Connecting to MySQL at {DB_HOST}:{DB_PORT} as '{DB_USER}'…")
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASSWORD,
            charset="utf8mb4",
        )
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.close()
        print(f"[OK] Database '{DB_NAME}' ready.")
    except pymysql.OperationalError as exc:
        print(f"[ERROR] MySQL connection failed: {exc}")
        print("\nCheck that:")
        print("  1. MySQL Server is running")
        print("  2. DB_USER / DB_PASSWORD in .env are correct")
        sys.exit(1)


def create_tables():
    print("Creating ORM tables…")
    # Import models so SQLAlchemy knows about them
    from app.database.db import engine, Base
    from app.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("[OK] Tables created (or already exist).")


if __name__ == "__main__":
    create_database()
    create_tables()
    print("\n[SUCCESS] Setup complete! You can now run:")
    print("   venv\\Scripts\\uvicorn app.main:app --reload")
    print("   venv\\Scripts\\streamlit run ui\\streamlit_app.py")
