"""
Aspect-based logging utility.
Decorates service functions to automatically log entry, exit, duration and exceptions.
"""

import logging
import os
import time
import functools
from pathlib import Path

# ── Setup log directory and file ──────────────────────────────────────────────
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# ── Logger configuration ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)


def log_call(func):
    """
    AOP-style decorator.
    Logs function entry / exit / duration / exceptions automatically.
    Works on both sync and async functions.
    """
    logger = get_logger(func.__module__)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger.info("→ %s() called", func.__name__)
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info("← %s() succeeded in %.1f ms", func.__name__, elapsed)
            return result
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("✗ %s() raised %s after %.1f ms: %s",
                         func.__name__, type(exc).__name__, elapsed, exc)
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger.info("→ %s() called", func.__name__)
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info("← %s() succeeded in %.1f ms", func.__name__, elapsed)
            return result
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("✗ %s() raised %s after %.1f ms: %s",
                         func.__name__, type(exc).__name__, elapsed, exc)
            raise

    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper