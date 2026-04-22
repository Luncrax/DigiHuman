"""
Logging module for Virtual Human Assistant
Provides standardized logging functionality across the application
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.core.config import config


def setup_logger(
    name: str = __name__,
    log_file: Optional[str] = None,
    level: str = None,
    format_string: str = None
) -> logging.Logger:
    """
    Set up a logger with specified configuration
    
    Args:
        name: Name of the logger
        log_file: Path to log file (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Log message format
    
    Returns:
        Configured logger instance
    """
    # Use default values from config if not provided
    if level is None:
        level = config.LOG_LEVEL
    
    if log_file is None:
        log_file = config.LOG_FILE
    
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent adding multiple handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Name of the logger
    
    Returns:
        Configured logger instance
    """
    return setup_logger(name)


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function calls
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Calling function: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Function {func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Function {func.__name__} failed with error: {str(e)}")
                raise
        return wrapper
    return decorator


# Create a global logger instance for the application
app_logger = get_logger("VirtualHumanAssistant")


# Convenience functions for different log levels
def log_debug(message: str, logger: logging.Logger = None):
    """Log a debug message"""
    if logger is None:
        logger = app_logger
    logger.debug(message)


def log_info(message: str, logger: logging.Logger = None):
    """Log an info message"""
    if logger is None:
        logger = app_logger
    logger.info(message)


def log_warning(message: str, logger: logging.Logger = None):
    """Log a warning message"""
    if logger is None:
        logger = app_logger
    logger.warning(message)


def log_error(message: str, logger: logging.Logger = None):
    """Log an error message"""
    if logger is None:
        logger = app_logger
    logger.error(message)


def log_critical(message: str, logger: logging.Logger = None):
    """Log a critical message"""
    if logger is None:
        logger = app_logger
    logger.critical(message)


# Context manager for logging execution time
class LogExecutionTime:
    def __init__(self, logger: logging.Logger = None, message: str = "Operation"):
        self.logger = logger or app_logger
        self.message = message
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.message}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = end_time - self.start_time
        if exc_type is None:
            self.logger.info(f"Completed {self.message} in {duration.total_seconds():.2f}s")
        else:
            self.logger.error(f"Failed {self.message} after {duration.total_seconds():.2f}s with error: {exc_val}")
