"""Logging configuration using loguru"""

import sys
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()

# Console output
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# File output with rotation
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

logger.add(
    "logs/trading_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# Export logger
__all__ = ["logger"]