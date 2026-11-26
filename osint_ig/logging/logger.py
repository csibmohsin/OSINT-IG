"""Structured console logger for OSINT IG services."""
import logging
import os


def get_logger(name: str = "osint_ig") -> logging.Logger:
    """Return a configured logger without duplicating handlers."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    level_name = os.getenv("OSINT_IG_LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    return logger
