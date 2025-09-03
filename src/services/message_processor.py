"""
Message processor for handling Slack events from Service Bus queue.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Import plugin system
from ..plugins.loader import plugin_loader
from plugins.base import PluginResponse
from ..utils.deduplication import is_duplicate_message, generate_message_id

logger = logging.getLogger(__name__)


class SlackMessageProcessor:
    """
    Processes Slack messages from Service Bus queue using plugins.
    """
    
    def __init__(self):
        """Initialize the message processor."""
        self.slack_client = None
        self._init_slack_client()
        self._init_plugins()
    
    def _init_slack_client(self):
        """Initialize Slack client."""
        bot_token = os.environ.get("SLACK_BOT_TOKEN")
        if not bot_token:
            logger.error("SLACK_BOT_TOKEN not configured")
            return
        
        self.slack_client = WebClient(token=bot_token)
        logger.info("Slack client initialized successfully")
    
    def _init_plugins(self):
        """Initialize plugin loader."""
        try:
            plugin_loader.load_plugins()
            logger.info(f"Plugin loader initialized with {len(plugin_loader.plugins)} plugins")
        except Exception as e:
            logger.error(f"Failed to initialize plugins: {e}")
    
    def process_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Process a message from the Service Bus queue.
        
        Args:
            message_data: Dictionary containing the Slack event data
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            message_id = generate_message_id(message_data)
            logger.info(
                "Processing message from Service Bus", 
                extra={
                    "message_type": message_data.get("type"),
                    "message_id": message_id,
                    "user_id": message_data.get("user_id"),
                    "channel_id": message_data.get("channel_id")
                }
            )
            
            # Check for duplicates
            if is_duplicate_message(message_data):
                logger.info(f"Skipping duplicate message: {message_id}")
                return True  # Return True to prevent retry
            
            # Validate message data
            if not self._validate_message_data(message_data):
                logger.error("Invalid message data", extra={"message_data": message_data})
                return False
            
            # Process with plugins
            response = plugin_loader.process_message(message_data)
            
            if response:
                # Send response back to Slack
                success = self._send_slack_response(message_data, response)
                if success:
                    logger.info("Message processed and response sent successfully")
                    return True
                else:
                    logger.error("Failed to send response to Slack")
                    return False
            else:
                logger.info("Plugin processed message but returned no response")
                return True
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            # Try to send error message to user
            self._send_error_response(message_data, str(e))
            return False
    
    def _validate_message_data(self, message_data: Dict[str, Any]) -> bool:
        """
        Validate that message data contains required fields.
        
        Args:
            message_data: Message data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["type", "user_id", "channel_id", "text"]
        
        for field in required_fields:
            if field not in message_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        if message_data["type"] not in ["app_mention"]:
            logger.error(f"Unsupported message type: {message_data['type']}")
            return False
        
        return True
    
    def _send_slack_response(self, message_data: Dict[str, Any], response: PluginResponse) -> bool:
        """
        Send response back to Slack.
        
        Args:
            message_data: Original message data
            response: Plugin response to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.slack_client:
            logger.error("Slack client not initialized")
            return False
        
        try:
            # Determine target channel
            target_channel = self._get_target_channel(message_data, response)
            
            if response.response_type == "none":
                logger.info("Response type is 'none', skipping Slack message")
                return True
            
            # Prepare message data
            message_kwargs = {
                "channel": target_channel,
                "text": response.text or "Mensaje procesado"
            }
            
            # Add blocks if available
            if response.blocks:
                message_kwargs["blocks"] = response.blocks
            
            # Add thread timestamp if replying in thread
            if response.thread_ts:
                message_kwargs["thread_ts"] = response.thread_ts
            elif message_data.get("timestamp"):
                # Reply in thread to original message
                message_kwargs["thread_ts"] = message_data["timestamp"]
            
            # Send main response
            result = self.slack_client.chat_postMessage(**message_kwargs)
            
            if result["ok"]:
                logger.info(f"Successfully sent message to channel {target_channel}")
                
                # Send additional responses if any
                if response.additional_responses:
                    self._send_additional_responses(response.additional_responses)
                
                return True
            else:
                logger.error(f"Slack API error: {result}")
                return False
                
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Error sending Slack response: {e}")
            return False
    
    def _get_target_channel(self, message_data: Dict[str, Any], response: PluginResponse) -> str:
        """
        Determine target channel based on response type.
        
        Args:
            message_data: Original message data
            response: Plugin response
            
        Returns:
            str: Channel ID to send response to
        """
        if response.response_type == "dm":
            return message_data["user_id"]  # DM to the user
        elif response.response_type == "specific_channel" and response.channel:
            return response.channel
        else:
            # Default: respond in the same channel
            return message_data["channel_id"]
    
    def _send_additional_responses(self, additional_responses: list) -> None:
        """
        Send additional responses to other channels/users.
        
        Args:
            additional_responses: List of additional response dictionaries
        """
        for additional_response in additional_responses:
            try:
                if "channel" in additional_response and "text" in additional_response:
                    result = self.slack_client.chat_postMessage(
                        channel=additional_response["channel"],
                        text=additional_response["text"],
                        blocks=additional_response.get("blocks")
                    )
                    
                    if result["ok"]:
                        logger.info(f"Additional response sent to {additional_response['channel']}")
                    else:
                        logger.error(f"Failed to send additional response: {result}")
                        
            except Exception as e:
                logger.error(f"Error sending additional response: {e}")
    
    def _send_error_response(self, message_data: Dict[str, Any], error_message: str) -> None:
        """
        Send error response to user when processing fails.
        
        Args:
            message_data: Original message data
            error_message: Error message to display
        """
        if not self.slack_client:
            return
        
        try:
            user_id = message_data.get("user_id")
            channel_id = message_data.get("channel_id")
            
            if not user_id or not channel_id:
                return
            
            error_text = f"❌ <@{user_id}>, hubo un error procesando tu comando: {error_message}"
            
            self.slack_client.chat_postMessage(
                channel=channel_id,
                text=error_text
            )
            
            logger.info("Error response sent to user")
            
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")


# Global processor instance
message_processor = SlackMessageProcessor()
