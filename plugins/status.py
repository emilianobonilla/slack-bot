"""
Status plugin that shows bot status and health information.
"""
import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from .base import BasePlugin, PluginResponse


class StatusPlugin(BasePlugin):
    """
    Plugin for displaying bot status and health information.
    """
    
    def process(self, event_data: Dict[str, Any], matched_text: str) -> Optional[PluginResponse]:
        """
        Process status command and return bot status information.
        
        Args:
            event_data: Full Slack event data
            matched_text: The matched text ("status" or "estado")
            
        Returns:
            PluginResponse with status information
        """
        self.log_info("Processing status command")
        
        # Gather status information
        status_info = self._gather_status_info()
        
        # Create status response with blocks
        blocks = self._create_status_blocks(status_info)
        
        return PluginResponse(
            text="📊 Estado del Bot",
            blocks=blocks,
            response_type="channel"
        )
    
    def _gather_status_info(self) -> Dict[str, Any]:
        """Gather various status metrics."""
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            status_info = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "🟢 Operativo",
                "cpu_usage": f"{cpu_percent:.1f}%",
                "memory_usage": f"{memory.percent:.1f}%",
                "memory_used": f"{memory.used / (1024**3):.1f} GB",
                "memory_total": f"{memory.total / (1024**3):.1f} GB"
            }
        except Exception as e:
            # Fallback if psutil fails
            self.log_error(f"Error gathering system info: {e}")
            status_info = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "🟡 Información limitada",
                "cpu_usage": "N/A",
                "memory_usage": "N/A",
                "memory_used": "N/A",
                "memory_total": "N/A"
            }
        
        return status_info
    
    def _create_status_blocks(self, status_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create Slack blocks for status information display."""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Estado del Bot"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Estado:* {status_info['status']}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*🕒 Última verificación:*\\n{status_info['timestamp']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*💻 Uso de CPU:*\\n{status_info['cpu_usage']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*🧠 Uso de Memoria:*\\n{status_info['memory_usage']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*💾 Memoria:*\\n{status_info['memory_used']} / {status_info['memory_total']}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔧 Componentes:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "• ✅ Plugin System\\n" +
                           "• ✅ Azure Service Bus\\n" +
                           "• ✅ Slack API\\n" +
                           "• ✅ Azure Functions"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🔄 Para más información detallada, contacta al administrador."
                    }
                ]
            }
        ]
        
        return blocks
    
    def get_help_text(self) -> str:
        """Return help text for status plugin."""
        return "status|estado - Muestra el estado actual y métricas del bot"
