"""
Incident plugin for retrieving incident information.
"""
import re
import time
import random
from typing import Dict, Any, Optional, List
from .base import BasePlugin, PluginResponse


class IncidentPlugin(BasePlugin):
    """
    Plugin for handling incident-related queries.
    """
    
    def process(self, event_data: Dict[str, Any], matched_text: str) -> Optional[PluginResponse]:
        """
        Process incident query and return incident information.
        
        Args:
            event_data: Full Slack event data
            matched_text: The matched text containing incident ID
            
        Returns:
            PluginResponse with incident information
        """
        self.log_info("Processing incident command", matched_text=matched_text)
        
        # Extract incident ID from matched text
        incident_id = self._extract_incident_id(matched_text)
        
        if not incident_id:
            return PluginResponse(
                text="❌ No pude extraer el número del incidente. Formato esperado: 'incidente 123'",
                response_type="channel"
            )
        
        # Simulate API call delay
        self.log_info(f"Fetching incident information for ID: {incident_id}")
        
        # Simulate some processing time
        time.sleep(1)  # This would be an actual API call
        
        # Mock incident data
        incident_info = self._get_mock_incident_data(incident_id)
        
        # Create rich response with blocks
        blocks = self._create_incident_blocks(incident_info)
        
        return PluginResponse(
            text=f"📋 Información del Incidente #{incident_id}",
            blocks=blocks,
            response_type="channel"
        )
    
    def _extract_incident_id(self, matched_text: str) -> Optional[str]:
        """Extract incident ID from matched text."""
        match = re.search(r'incidente\s+(\d+)', matched_text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _get_mock_incident_data(self, incident_id: str) -> Dict[str, Any]:
        """
        Generate mock incident data.
        This would be replaced with actual API call in production.
        """
        # Mock data generation
        statuses = ["Abierto", "En Progreso", "Resuelto", "Cerrado"]
        priorities = ["Baja", "Media", "Alta", "Crítica"]
        assignees = ["Juan Pérez", "María García", "Carlos López", "Ana Martínez"]
        
        # Use incident_id as seed for consistent "random" data
        random.seed(int(incident_id))
        
        return {
            "id": incident_id,
            "title": f"Incidente de sistema #{incident_id}",
            "status": random.choice(statuses),
            "priority": random.choice(priorities),
            "assignee": random.choice(assignees),
            "created_at": "2025-09-03 10:30:00",
            "updated_at": "2025-09-03 14:15:00",
            "description": f"Descripción del incidente #{incident_id}. Problema reportado por usuario.",
            "resolution": "Investigando causa raíz del problema." if random.choice([True, False]) else "Resuelto mediante reinicio de servicio."
        }
    
    def _create_incident_blocks(self, incident_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create Slack blocks for incident information display."""
        
        # Priority emoji mapping
        priority_emojis = {
            "Baja": "🟢",
            "Media": "🟡", 
            "Alta": "🟠",
            "Crítica": "🔴"
        }
        
        # Status emoji mapping
        status_emojis = {
            "Abierto": "🆕",
            "En Progreso": "⚠️",
            "Resuelto": "✅",
            "Cerrado": "🔒"
        }
        
        priority_emoji = priority_emojis.get(incident_info["priority"], "⚪")
        status_emoji = status_emojis.get(incident_info["status"], "❓")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📋 Incidente #{incident_info['id']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{incident_info['title']}*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Estado:* {status_emoji} {incident_info['status']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Prioridad:* {priority_emoji} {incident_info['priority']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Asignado a:* {incident_info['assignee']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Creado:* {incident_info['created_at']}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Descripción:*\\n{incident_info['description']}"
                }
            }
        ]
        
        # Add resolution if available
        if incident_info.get('resolution'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Resolución:*\\n{incident_info['resolution']}"
                }
            })
        
        return blocks
    
    def get_help_text(self) -> str:
        """Return help text for incident plugin."""
        return "incidente <número> - Obtiene información detallada del incidente especificado"
