# =====================================================================
# Product Search Amazon — Utils: Logging Setup
# =====================================================================

import logging
import sys
from typing import Optional


def setup_logging(
    name: str = "AmazonProductSearch",
    level: int = logging.INFO,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configures and returns a logger with consistent formatting.
    """
    fmt = log_format or "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


def get_pipeline_logger(name: str = "AmazonProductSearch") -> logging.Logger:
    """
    Returns a pre-configured pipeline logger.
    """
    return logging.getLogger(name)