# logger_config.py

import logging
from logging.handlers import RotatingFileHandler


def setup_logger(name):
    """Create and configure a logger with specified name."""
    # Setup formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler("app.log", maxBytes=10000, backupCount=3)
    file_handler.setFormatter(formatter)

    # Create logger and set level
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # Set the default logging level
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Avoid logging being processed multiple times
    logger.propagate = False

    return logger
