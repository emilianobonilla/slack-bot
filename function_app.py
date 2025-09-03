import azure.functions as func
import logging
import json
import os
from slack_bolt import App
import hashlib
import hmac

# Import our app structure
try:
    from src.app import create_app
    from src.config import validate_configuration
except ImportError:
    # Fallback for when src module isn't available
    create_app = None
    validate_configuration = None

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Slack app
slack_app = None
try:
    if create_app:
        # Use our structured app creation
        slack_app = create_app()
        logging.info("Slack app initialized successfully using src.app")
    else:
        # Fallback to direct initialization
        slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
        slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
        
        if slack_bot_token and slack_signing_secret:
            slack_app = App(
                token=slack_bot_token,
                signing_secret=slack_signing_secret,
                process_before_response=True
            )
            logging.info("Slack app initialized successfully (fallback mode)")
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
    logging.info(f"Received Slack event request - Method: {req.method}, URL: {req.url}")
    
    if not slack_app:
        error_msg = "Slack app not configured. Please set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET."
        logging.error(error_msg)
        return func.HttpResponse(error_msg, status_code=503)
    
    try:
        # Get request headers and body
        timestamp = req.headers.get('X-Slack-Request-Timestamp')
        signature = req.headers.get('X-Slack-Signature')
        content_type = req.headers.get('Content-Type', '')
        body = req.get_body()
        
        logging.info(f"Request headers - Timestamp: {timestamp}, Signature: {signature[:20]}..., Content-Type: {content_type}")
        logging.info(f"Request body length: {len(body)} bytes")
        
        # Verify signature
        signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
        if not verify_slack_signature(signing_secret, timestamp, body, signature):
            logging.error("Slack signature verification failed")
            return func.HttpResponse("Unauthorized", status_code=401)
        
        logging.info("Slack signature verified successfully")
        
        # Parse body
        try:
            body_json = json.loads(body.decode('utf-8'))
            logging.info(f"Parsed JSON body: {json.dumps(body_json, indent=2)[:500]}...")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON body: {e}")
            return func.HttpResponse("Invalid JSON", status_code=400)
        
        # Handle URL verification challenge
        if body_json.get('type') == 'url_verification':
            challenge = body_json.get('challenge')
            logging.info(f"URL verification challenge received: {challenge}")
            return func.HttpResponse(challenge, mimetype="text/plain")
        
        # Process with Slack Bolt
        logging.info("Processing event with Slack Bolt")
        
        # Create a mock request object that Slack Bolt expects
        from slack_bolt.request import BoltRequest
        from slack_bolt.response import BoltResponse
        
        # Convert Azure Function request to Slack Bolt request format
        bolt_request = BoltRequest(
            body=body.decode('utf-8'),
            headers={
                'x-slack-request-timestamp': timestamp,
                'x-slack-signature': signature,
                'content-type': content_type
            }
        )
        
        # Process the request with Slack Bolt
        bolt_response: BoltResponse = slack_app.dispatch(bolt_request)
        
        logging.info(f"Slack Bolt response - Status: {bolt_response.status}, Body: {bolt_response.body[:200] if bolt_response.body else 'None'}...")
        
        # Return the response
        return func.HttpResponse(
            bolt_response.body or "OK",
            status_code=bolt_response.status,
            headers=dict(bolt_response.headers) if bolt_response.headers else None
        )
        
    except Exception as e:
        logging.error(f"Error processing Slack event: {e}", exc_info=True)
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

@app.route(route="test-settings", auth_level=func.AuthLevel.ANONYMOUS)
def test_settings(req: func.HttpRequest) -> func.HttpResponse:
    """Show current settings for debugging"""
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
    slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
    
    settings = {
        "slack_app_initialized": slack_app is not None,
        "slack_bot_token_present": bool(slack_bot_token),
        "slack_bot_token_length": len(slack_bot_token) if slack_bot_token else 0,
        "slack_bot_token_prefix": slack_bot_token[:12] + "..." if slack_bot_token else None,
        "slack_signing_secret_present": bool(slack_signing_secret),
        "slack_signing_secret_length": len(slack_signing_secret) if slack_signing_secret else 0,
        "slack_signing_secret_prefix": slack_signing_secret[:8] + "..." if slack_signing_secret else None,
        "python_path": os.environ.get("PYTHONPATH", "Not set"),
        "azure_functions_env": {
            "FUNCTIONS_WORKER_RUNTIME": os.environ.get("FUNCTIONS_WORKER_RUNTIME"),
            "FUNCTIONS_EXTENSION_VERSION": os.environ.get("FUNCTIONS_EXTENSION_VERSION"),
        },
        "src_module_available": create_app is not None,
        "initialization_errors": []
    }
    
    # Test importing src modules
    try:
        from src.app import create_app as test_create_app
        settings["src_import_test"] = "SUCCESS"
    except ImportError as e:
        settings["src_import_test"] = f"FAILED: {str(e)}"
        settings["initialization_errors"].append(f"src import failed: {str(e)}")
    
    # Test slack_bolt availability
    try:
        import slack_bolt
        settings["slack_bolt_version"] = getattr(slack_bolt, '__version__', 'unknown')
    except ImportError as e:
        settings["slack_bolt_available"] = f"FAILED: {str(e)}"
        settings["initialization_errors"].append(f"slack_bolt import failed: {str(e)}")
    
    return func.HttpResponse(
        json.dumps(settings, indent=2),
        mimetype="application/json"
    )

# Azure Function HTTP trigger for Slack slash commands
@app.route(route="slack/commands", auth_level=func.AuthLevel.ANONYMOUS)
def slack_commands(req: func.HttpRequest) -> func.HttpResponse:
    """Handle Slack slash commands via HTTP trigger"""
    logging.info(f"Received Slack command request - Method: {req.method}, URL: {req.url}")
    
    if not slack_app:
        error_msg = "Slack app not configured. Please set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET."
        logging.error(error_msg)
        return func.HttpResponse(error_msg, status_code=503)
    
    try:
        # Get request headers and body
        timestamp = req.headers.get('X-Slack-Request-Timestamp')
        signature = req.headers.get('X-Slack-Signature')
        content_type = req.headers.get('Content-Type', '')
        body = req.get_body()
        
        logging.info(f"Command request headers - Timestamp: {timestamp}, Signature: {signature[:20] if signature else None}..., Content-Type: {content_type}")
        logging.info(f"Command request body length: {len(body)} bytes")
        
        # Verify signature
        signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
        if not verify_slack_signature(signing_secret, timestamp, body, signature):
            logging.error("Slack signature verification failed for command")
            return func.HttpResponse("Unauthorized", status_code=401)
        
        logging.info("Slack command signature verified successfully")
        
        # Process with Slack Bolt
        logging.info("Processing slash command with Slack Bolt")
        
        # Create a mock request object that Slack Bolt expects
        from slack_bolt.request import BoltRequest
        from slack_bolt.response import BoltResponse
        
        # Convert Azure Function request to Slack Bolt request format
        bolt_request = BoltRequest(
            body=body.decode('utf-8'),
            headers={
                'x-slack-request-timestamp': timestamp,
                'x-slack-signature': signature,
                'content-type': content_type
            }
        )
        
        # Process the request with Slack Bolt
        bolt_response: BoltResponse = slack_app.dispatch(bolt_request)
        
        logging.info(f"Slack Bolt command response - Status: {bolt_response.status}, Body: {bolt_response.body[:200] if bolt_response.body else 'None'}...")
        
        # Return the response
        return func.HttpResponse(
            bolt_response.body or "OK",
            status_code=bolt_response.status,
            headers=dict(bolt_response.headers) if bolt_response.headers else None
        )
        
    except Exception as e:
        logging.error(f"Error processing Slack command: {e}", exc_info=True)
        return func.HttpResponse("Internal Server Error", status_code=500)
