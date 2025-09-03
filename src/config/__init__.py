"""Configuration module for the Slack bot."""

from .settings import (
    SlackConfig,
    AppConfig,
    slack_config,
    app_config,
    settings,  # Legacy
    validate_configuration,
)

__all__ = [
    "SlackConfig",
    "AppConfig", 
    "slack_config",
    "app_config",
    "settings",
    "validate_configuration",
]
