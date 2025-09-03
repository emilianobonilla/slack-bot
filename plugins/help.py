"""
Help plugin that shows available commands and plugins.
"""
from typing import Dict, Any, Optional, List
from .base import BasePlugin, PluginResponse


class HelpPlugin(BasePlugin):
    """
    Plugin for displaying available commands and help information.
    """
    
    def process(self, event_data: Dict[str, Any], matched_text: str) -> Optional[PluginResponse]:
        """
        Process help command and return available commands.
        
        Args:
            event_data: Full Slack event data
            matched_text: The matched text ("help" or "ayuda")
            
        Returns:
            PluginResponse with help information
        """
        self.log_info("Processing help command")
        
        # Create help response with blocks
        blocks = self._create_help_blocks()
        
        return PluginResponse(
            text="Help - Available Commands",
            blocks=blocks,
            response_type="channel"
        )
    
    def _create_help_blocks(self) -> List[Dict[str, Any]]:
        """Create Slack blocks for help information display."""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Bot Help"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hello! I'm your Slack bot. Here are the commands you can use:"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Available commands:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                "text": "• `@bot ping` - Verify connectivity\\n" +
                           "• `@bot incidente <number>` - Get incident information\\n" +
                           "• `@bot help` - Show this help\\n" +
                           "• `@bot status` - Show bot status"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*How to use:*\\n" +
                           "1. Mention the bot with `@bot` followed by the command\\n" +
                           "2. You can also send me a direct message\\n" +
                           "3. Use `/hello`, `/info`, `/help` as slash commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Examples:*\\n" +
                           "• `@bot ping`\\n" +
                           "• `@bot incidente 123`\\n" +
                           "• `@bot help`"
                }
            },
            {
                "type": "context",
                "elements": [
                [
                    {
                        "type": "mrkdwn",
                        "text": "Need additional help? Contact the system administrator."
                    }
                ]
        ]
        
        return blocks
    
    def get_help_text(self) -> str:
        """Return help text for help plugin."""
        return "help - Shows this list of available commands"
