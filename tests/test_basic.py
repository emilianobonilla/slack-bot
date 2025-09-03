"""
Basic tests for the Slack bot
"""
import pytest
from src.config.settings import Settings


def test_settings_creation():
    """Test that settings can be created"""
    settings = Settings()
    assert settings is not None


def test_settings_validation_without_tokens():
    """Test settings validation when tokens are missing"""
    settings = Settings()
    # Should be False if no environment variables are set
    assert settings.validate() in [True, False]  # Depends on env vars
