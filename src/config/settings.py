"""
Configuration settings for the Slack bot.
Manages environment variables and application settings.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SlackConfig:
    """Slack-specific configuration."""
    
    BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate that required Slack configuration is present."""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("SLACK_BOT_TOKEN is required")
        elif not cls.BOT_TOKEN.startswith("xoxb-"):
            errors.append("SLACK_BOT_TOKEN should start with 'xoxb-'")
            
        if not cls.SIGNING_SECRET:
            errors.append("SLACK_SIGNING_SECRET is required")
            
            
        return errors

class AppConfig:
    """General application configuration."""
    
    NAME: str = os.getenv("APP_NAME", "SlackBot")
    VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
    FUNCTIONS_WORKER_RUNTIME: str = os.getenv("FUNCTIONS_WORKER_RUNTIME", "python")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() == "production"

# Create singleton instances
slack_config = SlackConfig()
app_config = AppConfig()

# Legacy settings class for backwards compatibility
class Settings:
    """Legacy settings class - use slack_config and app_config instead."""
    
    def __init__(self):
        self.slack_bot_token: Optional[str] = slack_config.BOT_TOKEN or None
        self.slack_signing_secret: Optional[str] = slack_config.SIGNING_SECRET or None
        self.functions_worker_runtime: str = app_config.FUNCTIONS_WORKER_RUNTIME
        self.log_level: str = app_config.LOG_LEVEL
    
    def validate(self) -> bool:
        """Validate that required settings are present."""
        errors = slack_config.validate()
        return len(errors) == 0

def validate_configuration() -> tuple[bool, list[str]]:
    """
    Validate all configuration settings.
    
    Returns:
        tuple: (is_valid, error_list)
    """
    errors = slack_config.validate()
    
    # Add any additional validation here
    if app_config.LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        errors.append(f"Invalid LOG_LEVEL: {app_config.LOG_LEVEL}")
    
    return len(errors) == 0, errors

# Global settings instance (for backwards compatibility)
settings = Settings()
