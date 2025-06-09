"""
Logger Setup for Disaster Response System
Configures system-wide logging with proper formatting and rotation
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_size_mb: int = 50,
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup system-wide logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_size_mb: Maximum log file size in MB before rotation
        backup_count: Number of backup log files to keep
        console_output: Whether to output logs to console
    
    Returns:
        logging.Logger: Configured root logger
    """
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create custom formatter
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, date_format)
    
    # Get root logger and clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(numeric_level)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        try:
            # Create log directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size_mb * 1024 * 1024,  # Convert MB to bytes
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # If file logging fails, log to console
            console_logger = logging.getLogger(__name__)
            console_logger.error(f"Failed to setup file logging: {e}")
    
    # Setup specific loggers for different modules
    _setup_module_loggers(numeric_level)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.info(f"Log level: {log_level}")
    if log_file:
        logger.info(f"Log file: {log_file}")
    
    return root_logger


def _setup_module_loggers(log_level: int):
    """Setup specific loggers for different modules."""
    
    # Camera module logger
    camera_logger = logging.getLogger('camera_manager')
    camera_logger.setLevel(log_level)
    
    # Network module logger
    network_logger = logging.getLogger('network_manager')
    network_logger.setLevel(log_level)
    
    # GCP uploader logger
    gcp_logger = logging.getLogger('gcp_uploader')
    gcp_logger.setLevel(log_level)
    
    # GPS tracker logger
    gps_logger = logging.getLogger('gps_tracker')
    gps_logger.setLevel(log_level)
    
    # System monitor logger
    monitor_logger = logging.getLogger('system_monitor')
    monitor_logger.setLevel(log_level)
    
    # Config manager logger
    config_logger = logging.getLogger('config_manager')
    config_logger.setLevel(log_level)
    
    # Main application logger
    main_logger = logging.getLogger('main')
    main_logger.setLevel(log_level)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: str):
    """
    Change the log level for all loggers.
    
    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Update root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Update all handlers
    for handler in root_logger.handlers:
        handler.setLevel(numeric_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Log level changed to: {level}")


def add_file_handler(
    log_file: str,
    log_level: str = "INFO",
    max_size_mb: int = 50,
    backup_count: int = 5
) -> bool:
    """
    Add an additional file handler to the logging system.
    
    Args:
        log_file: Path to log file
        log_level: Logging level for this handler
        max_size_mb: Maximum file size before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        bool: True if handler added successfully
    """
    try:
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create log directory
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Added file handler: {log_file}")
        return True
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to add file handler: {e}")
        return False


def log_system_info():
    """Log system information for debugging."""
    logger = logging.getLogger(__name__)
    
    try:
        import platform
        import psutil
        
        logger.info("=== System Information ===")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Architecture: {platform.architecture()[0]}")
        logger.info(f"Processor: {platform.processor()}")
        
        # Memory info
        memory = psutil.virtual_memory()
        logger.info(f"Total memory: {memory.total / (1024**3):.1f} GB")
        logger.info(f"Available memory: {memory.available / (1024**3):.1f} GB")
        
        # Disk info
        disk = psutil.disk_usage('/')
        logger.info(f"Total disk space: {disk.total / (1024**3):.1f} GB")
        logger.info(f"Free disk space: {disk.free / (1024**3):.1f} GB")
        
        # CPU info
        logger.info(f"CPU cores: {psutil.cpu_count()}")
        logger.info(f"CPU frequency: {psutil.cpu_freq().current:.0f} MHz")
        
        logger.info("=== End System Information ===")
        
    except Exception as e:
        logger.error(f"Failed to log system information: {e}")


class ContextFilter(logging.Filter):
    """Custom filter to add context information to log records."""
    
    def __init__(self, device_id: str = "unknown"):
        """
        Initialize context filter.
        
        Args:
            device_id: Device identifier to add to logs
        """
        super().__init__()
        self.device_id = device_id
    
    def filter(self, record):
        """Add context information to log record."""
        record.device_id = self.device_id
        return True


def add_context_filter(device_id: str):
    """
    Add context filter to all handlers.
    
    Args:
        device_id: Device identifier for context
    """
    context_filter = ContextFilter(device_id)
    
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(context_filter)
    
    # Update formatter to include device ID
    new_format = f"%(asctime)s - [{device_id}] - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(new_format, "%Y-%m-%d %H:%M:%S")
    
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Added context filter with device ID: {device_id}")


# Convenience function for emergency logging when main logging fails
def emergency_log(message: str, level: str = "ERROR"):
    """
    Emergency logging function for when main logging system fails.
    
    Args:
        message: Message to log
        level: Log level
    """
    try:
        timestamp = logging.Formatter().formatTime(logging.LogRecord(
            name="emergency", level=0, pathname="", lineno=0,
            msg="", args=(), exc_info=None
        ))
        
        emergency_message = f"{timestamp} - EMERGENCY - {level} - {message}"
        
        # Try to write to console
        print(emergency_message, file=sys.stderr)
        
        # Try to write to a basic log file
        try:
            with open("/tmp/disaster-camera-emergency.log", "a") as f:
                f.write(emergency_message + "\n")
        except Exception:
            pass  # If even this fails, we've done our best
            
    except Exception:
        # Last resort - basic print
        print(f"EMERGENCY: {message}", file=sys.stderr) 