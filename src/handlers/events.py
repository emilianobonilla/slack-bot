"""
Event handlers for Slack events like app mentions, reactions, etc.
"""
import os
import json
from slack_bolt import App, Say, Ack
from slack_bolt.context.say import Say
from slack_bolt.context.ack import Ack
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from ..utils.logging import SlackEventLogger

logger = SlackEventLogger(__name__)
def handle_app_mention(event, say: Say, ack: Ack, client, body):
    """
    Handle when the bot is mentioned in a channel.
    Sends the event to Service Bus for asynchronous processing.
    
    Args:
        event: The app mention event data
        say: Function to send a message
        ack: Function to acknowledge the event
        client: Slack client
        body: Full request body
    """
    user = event.get("user")
    channel = event.get("channel")
    text = event.get("text", "")
    timestamp = event.get("ts")
    
    # Create unique event ID for early deduplication
    event_id = f"{user}_{channel}_{timestamp}"
    
    # EARLY deduplication check - before ack()
    from ..utils.early_dedup import is_duplicate_or_processing, mark_event_completed
    if is_duplicate_or_processing(event_id):
        logger.logger.warning(f"Duplicate/processing app_mention detected, ignoring: {event_id}")
        ack()  # Still acknowledge to Slack
        return
    
    # Acknowledge immediately to avoid timeout
    ack()
    
    logger.log_event("app_mention", event, event_id=event_id)
    
    try:
        # Send immediate acknowledgment to user with message preview
        message_preview = text[:100].replace('<@U', '<@').replace('>', '') if len(text) > 100 else text.replace('<@U', '<@').replace('>', '')
        
        say(
            text=f"<@{user}>, I received your message: '*{message_preview}*' and I'm processing it... (ID: {event_id[-8:]})",
            channel=channel
        )
        
        # Prepare event data for Service Bus
        event_data = {
            "type": "app_mention",
            "event": event,
            "user_id": user,
            "channel_id": channel,
            "text": text,
            "timestamp": event.get("ts"),
            "team_id": body.get("team_id"),
            "api_app_id": body.get("api_app_id"),
            "processed_at": None,
            "response_url": None  # We'll use the channel_id to respond
        }
        
        # Send to Service Bus for processing
        success = _send_to_service_bus(event_data)
        
        if success:
            logger.logger.info(
                "Event sent to Service Bus for processing", 
                user_id=user, 
                channel_id=channel,
                text_preview=text[:50],
                event_id=event_id,
                message_length=len(text)
            )
            
            # Mark event as completed
            mark_event_completed(event_id)
        else:
            # Fallback: send error message
            say(
                text=f"<@{user}>, there was a problem processing your message. Please try again.",
                channel=channel
            )
            logger.logger.error(
                "Failed to send event to Service Bus", 
                user_id=user, 
                channel_id=channel
            )
            
            # Mark event as completed even on failure
            mark_event_completed(event_id)
            
    except Exception as e:
        logger.log_error(e, "Error handling app mention", user_id=user, channel_id=channel)
        
        # Mark event as completed even on exception
        mark_event_completed(event_id)
        
        try:
            # Try to send error response
            say(
                text=f"<@{user}>, an unexpected error occurred. Please try again.",
                channel=channel
            )
        except:
            # If we can't even send an error message, just log it
            logger.logger.error("Failed to send error response to user")


def _send_to_service_bus(event_data):
    """
    Send event data to Azure Service Bus queue.
    
    Args:
        event_data: Dictionary containing event information
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        connection_string = os.environ.get("SERVICE_BUS_CONNECTION_STRING")
        if not connection_string:
            logger.logger.error("SERVICE_BUS_CONNECTION_STRING not configured")
            return False
        
        # Generate unique message ID for deduplication
        import hashlib
        message_components = [
            event_data.get("user_id", ""),
            event_data.get("channel_id", ""),
            event_data.get("timestamp", ""),
            event_data.get("text", "")[:100]
        ]
        message_content = "|".join(str(c) for c in message_components)
        message_id = hashlib.md5(message_content.encode()).hexdigest()
        
        # Create Service Bus client
        with ServiceBusClient.from_connection_string(connection_string) as client:
            # Get queue sender
            with client.get_queue_sender(queue_name="slack-events") as sender:
                
                # Create message
                message_body = json.dumps(event_data)
                message = ServiceBusMessage(message_body)
                
                # Set unique message ID for Service Bus deduplication
                message.message_id = message_id
                
                # Add message properties for routing and debugging
                message.application_properties = {
                    "event_type": event_data.get("type", "unknown"),
                    "user_id": event_data.get("user_id"),
                    "channel_id": event_data.get("channel_id"),
                    "timestamp": event_data.get("timestamp"),
                    "message_id": message_id
                }
                
                # Send message
                sender.send_messages(message)
                logger.logger.info(
                    "Message sent to Service Bus queue", 
                    queue="slack-events",
                    message_id=message_id
                )
                return True
                
    except Exception as e:
        logger.logger.error(f"Error sending message to Service Bus: {e}")
        return False

def handle_reaction_added(event, ack: Ack):
    """
    Handle when a reaction is added to a message.
    
    Args:
        event: The reaction_added event data
        ack: Function to acknowledge the event
    """
    ack()
    logger.log_event("reaction_added", event)
    
    reaction = event.get("reaction")
    user = event.get("user")
    
    logger.logger.info("Reaction added", reaction=reaction, user_id=user)

def handle_team_join(event, say: Say, ack: Ack):
    """
    Handle when a new user joins the team.
    
    Args:
        event: The team_join event data
        say: Function to send a message
        ack: Function to acknowledge the event
    """
    ack()
    logger.log_event("team_join", event)
    
    user = event.get("user", {})
    user_id = user.get("id")
    user_name = user.get("name", "nuevo miembro")
    
    if user_id:
        # Send welcome message to the user
        welcome_message = f"Welcome to the team, {user_name}! I'm the Slack bot and I'm here to help you."
        
        try:
            say(
                text=welcome_message,
                channel=user_id  # Send DM to new user
            )
            logger.logger.info("Sent welcome message", user_id=user_id, user_name=user_name)
        except Exception as e:
            logger.log_error(e, "Failed to send welcome message", user_id=user_id)

def register_event_handlers(app: App) -> None:
    """
    Register all event handlers with the Slack app.
    
    Args:
        app: The Slack Bolt app instance
    """
    logger.logger.info("Registering event handlers")
    
    # App mentions - when bot is @ mentioned
    app.event("app_mention")(handle_app_mention)
    
    # Reactions - when users add reactions to messages
    app.event("reaction_added")(handle_reaction_added)
    
    # Team events - new members joining
    app.event("team_join")(handle_team_join)
    
    logger.logger.info("Event handlers registered successfully")
