"""Logging configuration."""

import logging
import logging.handlers
import os
from datetime import datetime

# Create logs directory
LOGS_DIR = os.getenv('LOGS_DIR', 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Log level from environment
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Format string
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_logger(name):
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Set level
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (rotating)
        log_file = os.path.join(LOGS_DIR, f'momo_tracker_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


# Pre-configured loggers
app_logger = get_logger('momo_tracker.app')
db_logger = get_logger('momo_tracker.db')
api_logger = get_logger('momo_tracker.api')
parser_logger = get_logger('momo_tracker.parser')
