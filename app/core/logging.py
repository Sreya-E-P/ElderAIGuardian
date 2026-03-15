"""
Logging Configuration with Azure Application Insights
"""

import sys
import logging
from loguru import logger
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from app.core.config import settings

class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru"""
    
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
            
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
            
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    """Setup logging with Azure Application Insights"""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO" if not settings.DEBUG else "DEBUG",
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler for production
    if settings.is_production:
        logger.add(
            "logs/elderai.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            level="INFO"
        )
        
        # Configure Azure Application Insights
        if settings.APPINSIGHTS_CONNECTION_STRING:
            try:
                configure_azure_monitor(
                    connection_string=settings.APPINSIGHTS_CONNECTION_STRING,
                    logger_name=__name__,
                    instrumentation_options={
                        "azure_sdk": {"enabled": True},
                        "fastapi": {"enabled": True},
                        "django": {"enabled": False},
                        "flask": {"enabled": False},
                        "psycopg2": {"enabled": True},
                        "requests": {"enabled": True},
                        "urllib": {"enabled": True},
                        "urllib3": {"enabled": True},
                    }
                )
                logger.info("Azure Application Insights configured")
            except Exception as e:
                logger.error(f"Failed to configure Application Insights: {e}")
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    logger.info(f"Logging configured for {settings.APP_ENV} environment")

def get_tracer(name: str):
    """Get OpenTelemetry tracer"""
    return trace.get_tracer(name)

def trace_function(func):
    """Decorator to trace function execution"""
    def wrapper(*args, **kwargs):
        tracer = get_tracer(func.__module__)
        with tracer.start_as_current_span(func.__name__) as span:
            span.set_attribute("function", func.__name__)
            span.set_attribute("module", func.__module__)
            try:
                result = func(*args, **kwargs)
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    return wrapper