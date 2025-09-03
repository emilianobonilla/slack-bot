"""
Slash command handlers for the Slack bot.
"""
from slack_bolt import App, Ack, Respond
from slack_bolt.context.ack import Ack
from slack_bolt.context.respond import Respond
from ..utils.logging import SlackEventLogger
from ..config import app_config

logger = SlackEventLogger(__name__)

def handle_hello_command(ack: Ack, respond: Respond, command):
    """
    Handle the /hello slash command.
    
    Args:
        ack: Function to acknowledge the command
        respond: Function to respond to the command
        command: The command payload
    """
    ack()
    
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    text = command.get("text", "").strip()
    
    logger.log_command("/hello", user_id, channel_id, text=text)
    
    if text:
        response = f"Hello! You told me: '{text}'"
    else:
        response = f"Hello <@{user_id}>! How are you?"
    
    respond(response)

def handle_info_command(ack: Ack, respond: Respond, command):
    """
    Handle the /info slash command - shows bot information.
    
    Args:
        ack: Function to acknowledge the command
        respond: Function to respond to the command
        command: The command payload
    """
    ack()
    
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    
    logger.log_command("/info", user_id, channel_id)
    
    info_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Info - {app_config.NAME}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Version:* {app_config.VERSION}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Environment:* {app_config.ENVIRONMENT}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Available commands:*\\n• `/hello [message]` - Greet the bot\\n• `/info` - Show bot information\\n• `/help` - Show help"
            }
        }
    ]
    
    respond(blocks=info_blocks)

def handle_help_command(ack: Ack, respond: Respond, command):
    """
    Handle the /help slash command - shows available commands.
    
    Args:
        ack: Function to acknowledge the command
        respond: Function to respond to the command
        command: The command payload
    """
    ack()
    
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    
    logger.log_command("/help", user_id, channel_id)
    
    help_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Help - Bot Commands"
            }
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
                "text": "• `/hello [optional message]`\\n  Greet the bot with an optional message"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "• `/info`\\n  Muestra información sobre el bot"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "• `/help`\\n  Muestra esta ayuda"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*También puedes:*\\n• Mencionarme con `@{app_config.NAME}` en cualquier canal\\n• Enviarme un mensaje directo"
            }
        }
    ]
    
    respond(blocks=help_blocks)

def register_command_handlers(app: App) -> None:
    """
    Register all slash command handlers with the Slack app.
    
    Args:
        app: The Slack Bolt app instance
    """
    logger.logger.info("Registering command handlers")
    
    # Basic commands
    app.command("/hello")(handle_hello_command)
    app.command("/info")(handle_info_command)
    app.command("/help")(handle_help_command)
    
    logger.logger.info("Command handlers registered successfully")
