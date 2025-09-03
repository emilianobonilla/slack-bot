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
            text="🆘 Ayuda - Comandos disponibles",
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
                    "text": "🤖 Ayuda del Bot"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "¡Hola! Soy tu bot de Slack. Aquí están los comandos que puedes usar:"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 Comandos disponibles:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "• `@bot ping` - Verifica conectividad\\n" +
                           "• `@bot incidente <número>` - Obtiene información de incidente\\n" +
                           "• `@bot help` o `@bot ayuda` - Muestra esta ayuda\\n" +
                           "• `@bot status` o `@bot estado` - Muestra estado del bot"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💡 Cómo usar:*\\n" +
                           "1. Menciona al bot con `@bot` seguido del comando\\n" +
                           "2. También puedes enviarme un mensaje directo\\n" +
                           "3. Usa `/hello`, `/info`, `/help` como comandos slash"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📝 Ejemplos:*\\n" +
                           "• `@bot ping`\\n" +
                           "• `@bot incidente 123`\\n" +
                           "• `@bot help`"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💬 ¿Necesitas ayuda adicional? Contacta al administrador del sistema."
                    }
                ]
            }
        ]
        
        return blocks
    
    def get_help_text(self) -> str:
        """Return help text for help plugin."""
        return "help|ayuda - Muestra esta lista de comandos disponibles"
