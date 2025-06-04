# app/core/logger.py
from loguru import logger
import sys
from app.core.config import settings

def setup_logger(debug: bool = False):
    """Setup the logger with different levels and formats.
    
    Args:
        log_file: Path to log file (if None, logging to file is disabled)
        debug: Whether to enable debug logging
    """
    logger.remove()  # Clear default handlers

    format=(
         "[<red>{time:HH:mm:ss}</red>] | "
         "<cyan>{name}.{function}.{line}</cyan> | "
         "<yellow>{level}</yellow> | "
         "<cyan>{message}</cyan>"
     )

    logger.add(sys.stderr,
               level="DEBUG" if debug else "INFO",
               format=format,
               colorize=True
               )

    return logger

# Initialize the logger
logger = setup_logger(debug=settings.DEBUG)