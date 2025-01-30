"""
Logging configuration for the application.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

from plane_to_teams.config import Config

def setup_logging(config: Config) -> logging.Logger:
    """
    Setup application logging.
    
    Args:
        config: Application configuration
        
    Returns:
        logging.Logger: The configured root logger
        
    Raises:
        ValueError: If the log level is invalid
    """
    # Validate log level
    try:
        log_level = getattr(logging, config.log_level.upper())
    except AttributeError:
        raise ValueError(f"Invalid log level: {config.log_level}")

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    root_logger.handlers = []

    # Create formatters
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup file handler
    file_handler = RotatingFileHandler(
        config.log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    root_logger.info("Logging configured with level %s", config.log_level)

    return root_logger 