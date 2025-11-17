"""
Centralized logging configuration for the application.
Provides different loggers for different parts of the system.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Logs directory
LOGS_DIR = Path(__file__).parent.parent.parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Log format
LOG_FORMAT = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# File handler configuration (10MB max per file, keep 3 backups)
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 3


def setup_logger(name, log_file, level=logging.INFO, also_console=True):
    """
    Set up a logger with file and optional console output.

    Args:
        name: Logger name (e.g., 'app', 'upload', 'csp')
        log_file: Filename for the log file (e.g., 'app.log')
        level: Logging level (default: INFO)
        also_console: Whether to also log to console (default: True)

    Returns:
        logging.Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOGS_DIR / log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if also_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def setup_all_loggers():
    """Set up all application loggers."""

    # Main app logger
    app_logger = setup_logger('app', 'app.log')

    # Upload and processing logger
    upload_logger = setup_logger('upload', 'upload.log')

    # CSP generation logger
    csp_logger = setup_logger('csp', 'csp_generation.log')

    # DAT processing logger
    dat_logger = setup_logger('dat', 'dat_processing.log')

    # Database operations logger
    db_logger = setup_logger('database', 'database.log')

    # Error logger (captures all errors)
    error_logger = setup_logger('error', 'error.log', level=logging.ERROR)

    return {
        'app': app_logger,
        'upload': upload_logger,
        'csp': csp_logger,
        'dat': dat_logger,
        'database': db_logger,
        'error': error_logger
    }


# Convenience functions for getting loggers
def get_app_logger():
    """Get the main application logger."""
    return logging.getLogger('app')


def get_upload_logger():
    """Get the upload/processing logger."""
    return logging.getLogger('upload')


def get_csp_logger():
    """Get the CSP generation logger."""
    return logging.getLogger('csp')


def get_dat_logger():
    """Get the DAT processing logger."""
    return logging.getLogger('dat')


def get_db_logger():
    """Get the database operations logger."""
    return logging.getLogger('database')


def get_error_logger():
    """Get the error logger."""
    return logging.getLogger('error')


# Initialize all loggers when this module is imported
LOGGERS = setup_all_loggers()
