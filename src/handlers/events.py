"""
Event handlers for Slack events like app mentions, reactions, etc.
"""
from slack_bolt import App, Say, Ack
from slack_bolt.context.say import Say
from slack_bolt.context.ack import Ack
from ..utils.logging import SlackEventLogger

logger = SlackEventLogger(__name__)

def handle_app_mention(event, say: Say, ack: Ack):
    """
    Handle when the bot is mentioned in a channel.
    
    Args:
        event: The app mention event data
        say: Function to send a message
        ack: Function to acknowledge the event
    """
    ack()
    logger.log_event("app_mention", event)
    
    user = event.get("user")
    channel = event.get("channel")
    text = event.get("text", "")
    
    # Simple response to mentions
    response = f"¡Hola <@{user}>! 👋 Soy tu bot de Slack. ¿En qué puedo ayudarte?"
    
    say(
        text=response,
        channel=channel
    )
    
    logger.logger.info("Responded to app mention", user_id=user, channel_id=channel)

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
        welcome_message = f"¡Bienvenido/a al equipo, {user_name}! 🎉 Soy el bot de Slack y estoy aquí para ayudarte."
        
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
