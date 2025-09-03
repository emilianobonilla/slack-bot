import azure.functions as func
import logging
import json
import os
from slack_bolt import App
import hashlib
import hmac

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Slack app (only if tokens are available)
slack_app = None
try:
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
    slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
    
    if slack_bot_token and slack_signing_secret:
        slack_app = App(
            token=slack_bot_token,
            signing_secret=slack_signing_secret,
            process_before_response=True
        )
        logging.info("Slack app initialized successfully")
    else:
        logging.warning("Slack tokens not found. Slack functionality will be disabled.")
except Exception as e:
    logging.error(f"Failed to initialize Slack app: {e}")

# Azure Functions app
app = func.FunctionApp()

# Example Slack event handler (registered only if slack_app is available)
if slack_app:
    @slack_app.message("hello")
    def handle_hello(message, say):
        """Handle hello messages"""
        user = message['user']
        say(f"Hi <@{user}>! 👋")
    
    # Example slash command handler
    @slack_app.command("/hello")
    def handle_hello_command(ack, respond, command):
        """Handle /hello slash command"""
        ack()
        respond(f"Hello {command['user_name']}! This is a response to your slash command.")

# Utility function to verify Slack request signature
def verify_slack_signature(signing_secret: str, timestamp: str, body: bytes, signature: str) -> bool:
    """Verify Slack request signature"""
    if not signing_secret:
        return False
    
    basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    my_signature = "v0=" + hmac.new(
        signing_secret.encode('utf-8'),
        basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(my_signature, signature)

# Azure Function HTTP trigger for Slack events
@app.route(route="slack/events", auth_level=func.AuthLevel.ANONYMOUS)
def slack_events(req: func.HttpRequest) -> func.HttpResponse:
    """Handle Slack events via HTTP trigger"""
    if not slack_app:
        return func.HttpResponse(
            "Slack app not configured. Please set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET.",
            status_code=503
        )
    
    try:
        # Get request headers and body
        timestamp = req.headers.get('X-Slack-Request-Timestamp')
        signature = req.headers.get('X-Slack-Signature')
        body = req.get_body()
        
        # Verify signature
        signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
        if not verify_slack_signature(signing_secret, timestamp, body, signature):
            return func.HttpResponse("Unauthorized", status_code=401)
        
        # Parse body
        body_json = json.loads(body.decode('utf-8'))
        
        # Handle URL verification challenge
        if body_json.get('type') == 'url_verification':
            return func.HttpResponse(
                body_json.get('challenge'),
                mimetype="text/plain"
            )
        
        # Process with Slack Bolt (simplified for now)
        return func.HttpResponse("OK", status_code=200)
        
    except Exception as e:
        logging.error(f"Error processing Slack event: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

# Simple HTTP trigger for testing
@app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    """Simple hello endpoint for testing"""
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = None
        else:
            name = req_body.get('name') if req_body else None
    
    if name:
        return func.HttpResponse(f"Hello, {name}! This Azure Function is working.")
    else:
        return func.HttpResponse(
            "Please pass a name in the query string or in the request body",
            status_code=400
        )
