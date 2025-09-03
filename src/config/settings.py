"""
Configuration settings for the Slack bot
"""
import os
from typing import Optional


class Settings:
    """Application settings"""
    
    def __init__(self):
        self.slack_bot_token: Optional[str] = os.getenv("SLACK_BOT_TOKEN")
        self.slack_signing_secret: Optional[str] = os.getenv("SLACK_SIGNING_SECRET")
        self.slack_app_token: Optional[str] = os.getenv("SLACK_APP_TOKEN")
        
        # Azure Functions settings
        self.functions_worker_runtime: str = os.getenv("FUNCTIONS_WORKER_RUNTIME", "python")
        
        # Logging level
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> bool:
        """Validate that required settings are present"""
        required_settings = [
            self.slack_bot_token,
            self.slack_signing_secret
        ]
        return all(setting is not None for setting in required_settings)


# Global settings instance
settings = Settings()
