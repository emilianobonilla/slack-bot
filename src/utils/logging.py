"""
Logging configuration and utilities for the Slack bot.
"""
import logging
import sys
from typing import Any, Dict
import structlog

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Filter by log level
            structlog.stdlib.filter_by_level,
            # Add log level to event dict
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add caller info for debugging
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            # Format the final output
            structlog.dev.ConsoleRenderer(colors=True)
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

class SlackEventLogger:
    """Helper class for logging Slack events consistently."""
    
    def __init__(self, logger_name: str):
        self.logger = structlog.get_logger(logger_name)
    
    def log_event(self, event_type: str, event_data: Dict[str, Any], **kwargs) -> None:
        """
        Log a Slack event with consistent structure.
        
        Args:
            event_type: Type of event (e.g., 'message', 'app_mention')
            event_data: Event payload from Slack
            **kwargs: Additional context to log
        """
        self.logger.info(
            "Processing Slack event",
            event_type=event_type,
            user_id=event_data.get("user"),
            channel_id=event_data.get("channel"),
            team_id=event_data.get("team"),
            **kwargs
        )
    
    def log_command(self, command: str, user_id: str, channel_id: str, **kwargs) -> None:
        """
        Log a Slack slash command.
        
        Args:
            command: The command that was executed
            user_id: ID of user who executed the command
            channel_id: ID of channel where command was executed
            **kwargs: Additional context to log
        """
        self.logger.info(
            "Processing slash command",
            command=command,
            user_id=user_id,
            channel_id=channel_id,
            **kwargs
        )
    
    def log_error(self, error: Exception, context: str, **kwargs) -> None:
        """
        Log an error with context.
        
        Args:
            error: The exception that occurred
            context: Description of what was happening when error occurred
            **kwargs: Additional context to log
        """
        self.logger.error(
            "Error occurred",
            context=context,
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs
        )
