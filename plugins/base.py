"""
Base plugin class for Slack bot plugins.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class PluginResponse:
    """
    Response object for plugin execution results.
    """
    def __init__(self, 
                 text: Optional[str] = None,
                 blocks: Optional[List[Dict]] = None,
                 response_type: str = "channel",
                 channel: Optional[str] = None,
                 thread_ts: Optional[str] = None,
                 additional_responses: Optional[List[Dict]] = None):
        """
        Initialize plugin response.
        
        Args:
            text: Simple text response
            blocks: Slack blocks for rich formatting
            response_type: "channel", "dm", "specific_channel", or "none"
            channel: Specific channel ID (for specific_channel type)
            thread_ts: Thread timestamp to reply in thread
            additional_responses: List of additional responses to send to other channels/DMs
        """
        self.text = text
        self.blocks = blocks
        self.response_type = response_type
        self.channel = channel
        self.thread_ts = thread_ts
        self.additional_responses = additional_responses or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization."""
        return {
            "text": self.text,
            "blocks": self.blocks,
            "response_type": self.response_type,
            "channel": self.channel,
            "thread_ts": self.thread_ts,
            "additional_responses": self.additional_responses
        }


class BasePlugin(ABC):
    """
    Abstract base class for all Slack bot plugins.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin configuration from YAML
        """
        self.name = config.get('name', self.__class__.__name__)
        self.patterns = config.get('patterns', [])
        self.config = config
        self.logger = logging.getLogger(f"plugin.{self.name}")
    
    @abstractmethod
    def process(self, event_data: Dict[str, Any], matched_text: str) -> Optional[PluginResponse]:
        """
        Process the matched message and return a response.
        
        Args:
            event_data: Full Slack event data
            matched_text: The text that matched the plugin pattern
            
        Returns:
            PluginResponse or None if no response needed
        """
        pass
    
    def get_help_text(self) -> str:
        """
        Return help text for this plugin.
        
        Returns:
            Help text describing what this plugin does
        """
        return f"Plugin {self.name}: No help text available"
    
    def can_handle(self, message_text: str) -> Optional[str]:
        """
        Check if this plugin can handle the given message.
        
        Args:
            message_text: The message text to check
            
        Returns:
            Matched text if plugin can handle, None otherwise
        """
        import re
        
        # Check if patterns should be treated as regex
        pattern_type = self.config.get('pattern_type', 'string')
        
        for pattern in self.patterns:
            if pattern_type == 'regex':
                # Treat as regex pattern
                try:
                    match = re.search(pattern, message_text, re.IGNORECASE)
                    if match:
                        return match.group(0)
                except re.error as e:
                    self.log_error(f"Invalid regex pattern '{pattern}': {e}")
                    continue
            else:
                # Simple string matching (case insensitive)
                if pattern.lower() in message_text.lower():
                    return pattern
        
        return None
    
    def log_info(self, message: str, **kwargs):
        """Log info message with plugin context."""
        self.logger.info(f"[{self.name}] {message}", extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with plugin context."""
        self.logger.error(f"[{self.name}] {message}", extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with plugin context."""
        self.logger.debug(f"[{self.name}] {message}", extra=kwargs)
