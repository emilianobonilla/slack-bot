"""
Simple ping plugin that responds with pong.
"""
from typing import Dict, Any, Optional
from .base import BasePlugin, PluginResponse


class PingPlugin(BasePlugin):
    """
    Simple ping-pong plugin for testing connectivity.
    """
    
    def process(self, event_data: Dict[str, Any], matched_text: str) -> Optional[PluginResponse]:
        """
        Process ping command and respond with pong.
        
        Args:
            event_data: Full Slack event data
            matched_text: The matched text ("ping")
            
        Returns:
            PluginResponse with pong message
        """
        self.log_info("Processing ping command", event_data=event_data)
        
        user_id = event_data.get('event', {}).get('user')
        channel_id = event_data.get('event', {}).get('channel')
        
        # Simple pong response
        response_text = f"🏓 ¡Pong! <@{user_id}>"
        
        return PluginResponse(
            text=response_text,
            response_type="channel"
        )
    
    def get_help_text(self) -> str:
        """Return help text for ping plugin."""
        return "ping - Responde con pong para verificar conectividad"
