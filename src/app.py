"""
Main Slack bot application using Slack Bolt framework.
"""
import logging
import structlog
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .config import slack_config, app_config, validate_configuration
from .handlers.events import register_event_handlers
from .handlers.commands import register_command_handlers
from .handlers.messages import register_message_handlers
from .utils.logging import setup_logging

# Setup structured logging
setup_logging(app_config.LOG_LEVEL)
logger = structlog.get_logger(__name__)

def create_app() -> App:
    """
    Create and configure the Slack Bot application.
    
    Returns:
        App: Configured Slack Bolt app instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Validate configuration
    is_valid, errors = validate_configuration()
    if not is_valid:
        error_msg = "Configuration validation failed: " + ", ".join(errors)
        logger.error("Configuration validation failed", errors=errors)
        raise ValueError(error_msg)
    
    logger.info("Creating Slack app", 
                app_name=app_config.NAME,
                version=app_config.VERSION,
                environment=app_config.ENVIRONMENT)
    
    # Create Slack app instance
    app = App(
        token=slack_config.BOT_TOKEN,
        signing_secret=slack_config.SIGNING_SECRET,
        process_before_response=True  # Important for avoiding 3-second timeout
    )
    
    # Register all handlers
    register_event_handlers(app)
    register_command_handlers(app)  
    register_message_handlers(app)
    
    logger.info("Slack app created successfully")
    return app

def start_socket_mode(app: App) -> None:
    """
    Start the bot in Socket Mode (for development).
    
    Args:
        app: The Slack Bolt app instance
    """
    if not slack_config.APP_TOKEN:
        raise ValueError("SLACK_APP_TOKEN is required for Socket Mode")
    
    logger.info("Starting Socket Mode handler")
    handler = SocketModeHandler(app, slack_config.APP_TOKEN)
    handler.start()

def main():
    """Main entry point for running the bot in development mode."""
    try:
        logger.info("Starting Slack bot", 
                   app_name=app_config.NAME,
                   version=app_config.VERSION)
        
        app = create_app()
        
        if slack_config.SOCKET_MODE:
            logger.info("Running in Socket Mode (development)")
            start_socket_mode(app)
        else:
            logger.warning("Socket Mode disabled - bot will only work with HTTP endpoints")
            logger.info("Use Azure Functions or another HTTP server for production")
            
    except Exception as e:
        logger.error("Failed to start Slack bot", error=str(e))
        raise

if __name__ == "__main__":
    main()
