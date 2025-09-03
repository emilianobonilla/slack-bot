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
                text="I couldn't extract the incident number. Expected format: 'incident 123'",
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
            text=f"Incident Information #{incident_id}",
            blocks=blocks,
            response_type="channel"
        )
    
    def _extract_incident_id(self, matched_text: str) -> Optional[str]:
        """Extract incident ID from matched text."""
        match = re.search(r'incident\\s+(\\d+)', matched_text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _get_mock_incident_data(self, incident_id: str) -> Dict[str, Any]:
        """
        Generate mock incident data.
        This would be replaced with actual API call in production.
        """
        # Mock data generation
        statuses = ["Open", "In Progress", "Resolved", "Closed"]
        priorities = ["Low", "Medium", "High", "Critical"]
        assignees = ["John Doe", "Jane Smith", "Mike Johnson", "Sarah Wilson"]
        
        # Use incident_id as seed for consistent "random" data
        random.seed(int(incident_id))
        
        return {
            "id": incident_id,
            "title": f"System Incident #{incident_id}",
            "status": random.choice(statuses),
            "priority": random.choice(priorities),
            "assignee": random.choice(assignees),
            "created_at": "2025-09-03 10:30:00",
            "updated_at": "2025-09-03 14:15:00",
            "description": f"Description of incident #{incident_id}. Issue reported by user.",
            "resolution": "Investigating root cause of the problem." if random.choice([True, False]) else "Resolved by service restart."
        }
    
    def _create_incident_blocks(self, incident_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create Slack blocks for incident information display."""
        
        # Priority markers (removed emojis)
        priority_markers = {
            "Low": "[LOW]",
            "Medium": "[MEDIUM]", 
            "High": "[HIGH]",
            "Critical": "[CRITICAL]"
        }
        
        # Status markers (removed emojis)
        status_markers = {
            "Open": "[OPEN]",
            "In Progress": "[IN PROGRESS]",
            "Resolved": "[RESOLVED]",
            "Closed": "[CLOSED]"
        }
        
        priority_marker = priority_markers.get(incident_info["priority"], "[UNKNOWN]")
        status_marker = status_markers.get(incident_info["status"], "[UNKNOWN]")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Incident #{incident_info['id']}"
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
                        "text": f"*Status:* {status_marker} {incident_info['status']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:* {priority_marker} {incident_info['priority']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Assigned to:* {incident_info['assignee']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Created:* {incident_info['created_at']}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\\n{incident_info['description']}"
                }
            }
        ]
        
        # Add resolution if available
        if incident_info.get('resolution'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Resolution:*\\n{incident_info['resolution']}"
                }
            })
        
        return blocks
    
    def get_help_text(self) -> str:
        """Return help text for incident plugin."""
        return "incident <number> - Gets detailed information for the specified incident"
