"""
Logging configuration
"""

import logging
from rich.logging import RichHandler


def setup_logger():
    """Setup main logger"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    return logging.getLogger("brand-analysis")


def get_logger(name: str):
    """Get logger for specific module"""
    return logging.getLogger(name)

