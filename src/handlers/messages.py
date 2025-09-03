"""
Message handlers for processing direct messages and message patterns.
"""
import re
from slack_bolt import App, Say, Ack
from slack_bolt.context.say import Say
from slack_bolt.context.ack import Ack
from ..utils.logging import SlackEventLogger

logger = SlackEventLogger(__name__)

def handle_direct_message(message, say: Say, ack: Ack):
    """
    Handle direct messages sent to the bot.
    
    Args:
        message: The message event data
        say: Function to send a message
        ack: Function to acknowledge the event
    """
    ack()
    logger.log_event("direct_message", message)
    
    user = message.get("user")
    text = message.get("text", "").strip()
    channel = message.get("channel")
    
    # Don't respond to bot messages to avoid loops
    if message.get("bot_id"):
        return
    
    if not text:
        return
    
    # Simple keyword-based responses
    text_lower = text.lower()
    
    if any(greeting in text_lower for greeting in ["hola", "hello", "hi", "hey"]):
        response = f"Hello <@{user}>! How can I help you today?"
    elif any(help_word in text_lower for help_word in ["ayuda", "help", "socorro"]):
        response = ("Of course! Here are some things I can do:\\n"
                   "• Respond to your messages\\n"
                   "• Use commands like `/hello`, `/info`, `/help`\\n"
                   "• Mention me in channels with `@bot`\\n\\n"
                   "What else can I help you with?")
    elif any(thanks in text_lower for thanks in ["gracias", "thanks", "thank you"]):
        response = "You're welcome! I'm always here to help."
    elif any(bye in text_lower for bye in ["adiós", "adios", "bye", "goodbye", "hasta luego"]):
        response = "Goodbye! Have an excellent day."
    else:
        # Default response for unrecognized messages
        response = (f"I received your message: \"{text}\"\\n\\n"
                   "I'm not sure how to respond to that specifically, but I'm here to help. "
                   "You can use `/help` to see what commands are available.")
    
    say(response)
    logger.logger.info("Responded to direct message", user_id=user, message_length=len(text))

def handle_keyword_mention(message, say: Say, ack: Ack):
    """
    Handle messages that contain specific keywords (not direct mentions).
    
    Args:
        message: The message event data
        say: Function to send a message
        ack: Function to acknowledge the event
    """
    ack()
    
    # Don't respond to bot messages
    if message.get("bot_id"):
        return
        
    text = message.get("text", "").lower()
    user = message.get("user")
    channel = message.get("channel")
    
    # Look for specific keywords that might require bot attention
    urgent_keywords = ["urgente", "emergency", "problema", "error", "help"]
    
    if any(keyword in text for keyword in urgent_keywords):
        logger.log_event("keyword_mention", message, keywords_found=True)
        
        response = (f"Hello <@{user}>! I saw you might need help. "
                   f"If you need assistance, you can mention me directly or use `/help` "
                   f"to see available commands.")
        
        say(response)
        logger.logger.info("Responded to keyword mention", user_id=user, channel_id=channel)

def register_message_handlers(app: App) -> None:
    """
    Register all message handlers with the Slack app.
    
    Args:
        app: The Slack Bolt app instance
    """
    logger.logger.info("Registering message handlers")
    
    # Direct messages - messages sent directly to the bot
    app.message(
        re.compile(r".*"),  # Match any message
        # Only in DM channels (channel type 'im')
        # Note: This will be filtered by channel type in the Slack app configuration
    )(handle_direct_message)
    
    # Keyword-based responses in channels (optional - be careful not to spam)
    # Uncomment the following lines if you want the bot to respond to keywords in channels
    # app.message(
    #     re.compile(r".*(urgente|emergency|problema|error).*", re.IGNORECASE)
    # )(handle_keyword_mention)
    
    logger.logger.info("Message handlers registered successfully")
