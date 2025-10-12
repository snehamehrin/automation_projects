"""
Structured logging configuration for the Reddit Sentiment Analyzer.

This module provides centralized logging configuration with structured
logging, correlation IDs, and proper formatting for production use.
"""

import logging
import logging.config
import sys
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import structlog
from structlog.stdlib import LoggerFactory

from ..config.settings import get_logging_settings


class CorrelationIDFilter(logging.Filter):
    """Filter to add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(self, '_correlation_id', '')
        return True


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', ''),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info', 'correlation_id']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for development logging."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET
        
        # Format the message
        formatted = super().format(record)
        
        # Add correlation ID if present
        correlation_id = getattr(record, 'correlation_id', '')
        if correlation_id:
            formatted = f"[{correlation_id}] {formatted}"
        
        return f"{color}{formatted}{reset}"


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    file_path: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> None:
    """
    Setup application logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format type (json, colored, simple)
        file_path: Optional file path for file logging
        correlation_id: Optional correlation ID for request tracking
    """
    # Create logs directory if it doesn't exist
    if file_path:
        log_file = Path(file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if format_type == "json" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    handlers = []
    
    # Console handler
    if format_type == "json":
        console_formatter = JSONFormatter()
    elif format_type == "colored":
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(CorrelationIDFilter())
    handlers.append(console_handler)
    
    # File handler
    if file_path:
        file_formatter = JSONFormatter()
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(CorrelationIDFilter())
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True
    )
    
    # Set correlation ID if provided
    if correlation_id:
        CorrelationIDFilter._correlation_id = correlation_id


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for request tracking.
    
    Args:
        correlation_id: Unique correlation ID
    """
    CorrelationIDFilter._correlation_id = correlation_id


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID.
    
    Returns:
        New correlation ID
    """
    return str(uuid.uuid4())


def log_function_call(func_name: str, **kwargs) -> None:
    """
    Log function call with parameters.
    
    Args:
        func_name: Function name
        **kwargs: Function parameters
    """
    logger = get_logger(__name__)
    logger.info("Function call", function=func_name, parameters=kwargs)


def log_performance(operation: str, duration: float, **kwargs) -> None:
    """
    Log performance metrics.
    
    Args:
        operation: Operation name
        duration: Duration in seconds
        **kwargs: Additional metrics
    """
    logger = get_logger(__name__)
    logger.info(
        "Performance metric",
        operation=operation,
        duration=duration,
        **kwargs
    )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log error with context.
    
    Args:
        error: Exception instance
        context: Additional context information
    """
    logger = get_logger(__name__)
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True
    )


def log_api_call(
    method: str,
    url: str,
    status_code: Optional[int] = None,
    duration: Optional[float] = None,
    **kwargs
) -> None:
    """
    Log API call details.
    
    Args:
        method: HTTP method
        url: API URL
        status_code: HTTP status code
        duration: Request duration
        **kwargs: Additional parameters
    """
    logger = get_logger(__name__)
    logger.info(
        "API call",
        method=method,
        url=url,
        status_code=status_code,
        duration=duration,
        **kwargs
    )


def log_data_processing(
    operation: str,
    input_count: int,
    output_count: int,
    duration: Optional[float] = None,
    **kwargs
) -> None:
    """
    Log data processing operations.
    
    Args:
        operation: Processing operation name
        input_count: Number of input items
        output_count: Number of output items
        duration: Processing duration
        **kwargs: Additional parameters
    """
    logger = get_logger(__name__)
    logger.info(
        "Data processing",
        operation=operation,
        input_count=input_count,
        output_count=output_count,
        retention_rate=(output_count / input_count * 100) if input_count > 0 else 0,
        duration=duration,
        **kwargs
    )


# Initialize logging with default settings
def initialize_logging() -> None:
    """Initialize logging with application settings."""
    settings = get_logging_settings()
    
    setup_logging(
        level=settings.level,
        format_type=settings.format,
        file_path=settings.file_path
    )
    
    logger = get_logger(__name__)
    logger.info("Logging initialized", level=settings.level, format=settings.format)


# Context manager for correlation ID
class CorrelationContext:
    """Context manager for correlation ID tracking."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or generate_correlation_id()
        self.original_correlation_id = None
    
    def __enter__(self):
        self.original_correlation_id = getattr(CorrelationIDFilter, '_correlation_id', None)
        set_correlation_id(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_correlation_id:
            set_correlation_id(self.original_correlation_id)
        else:
            CorrelationIDFilter._correlation_id = None
