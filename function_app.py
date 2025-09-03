import azure.functions as func
import logging
import json
import os
import sys
from slack_bolt import App
import hashlib
import hmac
from datetime import datetime

# Import our app structure
from src.app import create_app
from src.config import validate_configuration

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Slack app
try:
    slack_app = create_app()
    logging.info("Slack app initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Slack app: {e}")
    slack_app = None

# Azure Functions app
app = func.FunctionApp()

# Helper functions for health checks
def _check_configuration() -> bool:
    """Check if basic configuration is valid"""
    try:
        required_vars = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]
        return all(os.environ.get(var) for var in required_vars)
    except Exception:
        return False

def _check_src_modules() -> bool:
    """Check if src modules can be imported"""
    try:
        from src.app import create_app as test_create_app
        from src.config import validate_configuration as test_validate
        return True
    except ImportError:
        return False
    except Exception:
        return False

def _check_plugins() -> bool:
    """Check if plugin system is working"""
    try:
        from src.plugins.loader import PluginLoader
        loader = PluginLoader()
        loader.load_plugins()  # This loads plugins into loader.plugins
        return len(loader.plugins) > 0  # Check the loaded plugins
    except Exception as e:
        logging.error(f"Plugin check failed: {e}")
        return False

def _check_dependencies() -> bool:
    """Check if critical dependencies are available"""
    try:
        import slack_bolt
        import azure.servicebus
        import yaml
        return True
    except ImportError:
        return False
    except Exception:
        return False

def _get_plugin_details() -> dict:
    """Get detailed plugin information for debugging"""
    try:
        from src.plugins.loader import PluginLoader
        loader = PluginLoader()
        loader.load_plugins()
        
        plugin_details = {
            "total_loaded": len(loader.plugins),
            "plugins": []
        }
        
        for plugin in loader.plugins:
            plugin_details["plugins"].append({
                "name": plugin.name,
                "class": plugin.__class__.__name__,
                "patterns": getattr(plugin.config, 'patterns', []) if hasattr(plugin, 'config') else []
            })
        
        return plugin_details
    except Exception as e:
        return {"error": str(e), "total_loaded": 0, "plugins": []}

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

# Health check endpoint
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Comprehensive health check endpoint for monitoring and debugging"""
    try:
        # Collect health information
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": {
                "name": "slack-bot",
                "version": os.environ.get("APP_VERSION", "1.0.0"),
                "environment": os.environ.get("AZURE_FUNCTIONS_ENVIRONMENT", "unknown")
            },
            "components": {
                "slack_app": {
                    "status": "up" if slack_app is not None else "down",
                    "initialized": slack_app is not None
                },
                "azure_functions": {
                    "status": "up",
                    "runtime": os.environ.get("FUNCTIONS_WORKER_RUNTIME", "python"),
                    "version": os.environ.get("FUNCTIONS_EXTENSION_VERSION", "~4")
                },
                "python": {
                    "version": sys.version,
                    "version_info": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                },
                "configuration": {
                    "status": "up" if _check_configuration() else "down",
                    "slack_bot_token_present": bool(os.environ.get("SLACK_BOT_TOKEN")),
                    "slack_signing_secret_present": bool(os.environ.get("SLACK_SIGNING_SECRET")),
                    "service_bus_configured": bool(os.environ.get("SERVICE_BUS_CONNECTION_STRING"))
                }
            },
            "checks": {
                "src_modules": _check_src_modules(),
                "plugins": _check_plugins(),
                "dependencies": _check_dependencies()
            },
            "details": {
                "plugin_info": _get_plugin_details(),
                "config_file_exists": os.path.exists("plugins.yaml")
            }
        }
        
        # Determine overall status
        component_statuses = [comp.get("status", "unknown") for comp in health_data["components"].values()]
        check_results = [check for check in health_data["checks"].values()]
        
        if "down" in component_statuses or False in check_results:
            health_data["status"] = "degraded"
            status_code = 503
        else:
            health_data["status"] = "healthy"
            status_code = 200
            
        return func.HttpResponse(
            json.dumps(health_data, indent=2),
            mimetype="application/json",
            status_code=status_code
        )
        
    except Exception as e:
        logging.error(f"Health check failed: {e}", exc_info=True)
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }
        return func.HttpResponse(
            json.dumps(error_response, indent=2),
            mimetype="application/json",
            status_code=503
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

# Azure Function Service Bus trigger for processing Slack events
@app.service_bus_queue_trigger(
    arg_name="msg", 
    queue_name="slack-events",
    connection="SERVICE_BUS_CONNECTION_STRING"
)
def process_slack_events(msg: func.ServiceBusMessage) -> None:
    """Process Slack events from Service Bus queue using plugins"""
    logging.info(f"Processing Service Bus message - ID: {msg.message_id}, Delivery count: {msg.delivery_count}")
    
    try:
        # Parse message body
        message_body = msg.get_body().decode('utf-8')
        message_data = json.loads(message_body)
        
        logging.info(f"Parsed message data: {json.dumps(message_data, indent=2)[:500]}...")
        
        # Import and use message processor
        try:
            from src.services.message_processor import message_processor
            
            # Process the message
            success = message_processor.process_message(message_data)
            
            if success:
                logging.info("Message processed successfully")
            else:
                logging.warning("Message processing failed - may be duplicate or invalid")
                # Don't raise exception to avoid unnecessary retries for duplicates
                # The processor already handles duplicates and invalid messages
                
        except ImportError as e:
            logging.error(f"Failed to import message processor: {e}")
            # Fallback processing (optional)
            _fallback_message_processing(message_data)
            
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse message JSON: {e}")
        # This is a permanent error, don't retry
        return
    except Exception as e:
        logging.error(f"Error processing Service Bus message: {e}", exc_info=True)
        # Re-raise to trigger retry
        raise


def _fallback_message_processing(message_data):
    """
    Fallback message processing when main processor fails to import.
    """
    logging.info("Using fallback message processing")
    
    try:
        # Basic fallback - just send a simple response
        slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
        if not slack_bot_token:
            logging.error("SLACK_BOT_TOKEN not available for fallback processing")
            return
        
        from slack_sdk import WebClient
        client = WebClient(token=slack_bot_token)
        
        user_id = message_data.get("user_id")
        channel_id = message_data.get("channel_id")
        
        if user_id and channel_id:
            client.chat_postMessage(
                channel=channel_id,
                text=f"<@{user_id}>, system under maintenance. Please try again later."
            )
            logging.info("Fallback response sent to user")
            
    except Exception as e:
        logging.error(f"Fallback processing also failed: {e}")

# Debug endpoint for monitoring deduplication
@app.route(route="debug/dedup-stats", auth_level=func.AuthLevel.ANONYMOUS)
def dedup_stats(req: func.HttpRequest) -> func.HttpResponse:
    """Show deduplication statistics for debugging"""
    try:
        from src.utils.deduplication import message_deduplicator
        stats = message_deduplicator.get_stats()
        
        debug_info = {
            "deduplication_stats": stats,
            "timestamp": str(__import__('datetime').datetime.utcnow()),
            "environment": {
                "service_bus_configured": bool(os.environ.get("SERVICE_BUS_CONNECTION_STRING")),
                "slack_configured": bool(os.environ.get("SLACK_BOT_TOKEN"))
            }
        }
        
        return func.HttpResponse(
            json.dumps(debug_info, indent=2),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

# Test endpoint for plugin pattern matching
@app.route(route="debug/test-plugins", auth_level=func.AuthLevel.ANONYMOUS)
def test_plugins(req: func.HttpRequest) -> func.HttpResponse:
    """Test plugin pattern matching"""
    try:
        # Get test message from query parameters
        test_message = req.params.get('message', 'incidente 123')
        
        from src.plugins.loader import plugin_loader
        
        # Initialize plugins if not already loaded
        if not plugin_loader._loaded:
            plugin_loader.load_plugins()
        
        results = {
            "test_message": test_message,
            "plugins": [],
            "matched_plugin": None
        }
        
        # Test each plugin
        for plugin in plugin_loader.plugins:
            plugin_info = {
                "name": plugin.name,
                "patterns": plugin.patterns,
                "pattern_type": plugin.config.get('pattern_type', 'string'),
                "can_handle": False,
                "matched_text": None
            }
            
            matched_text = plugin.can_handle(test_message)
            if matched_text:
                plugin_info["can_handle"] = True
                plugin_info["matched_text"] = matched_text
                if not results["matched_plugin"]:
                    results["matched_plugin"] = plugin.name
            
            results["plugins"].append(plugin_info)
        
        return func.HttpResponse(
            json.dumps(results, indent=2),
            mimetype="application/json"
        )
        
    except Exception as e:
        import traceback
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc()
            }),
            status_code=500,
            mimetype="application/json"
        )

# Debug endpoint for recent events
@app.route(route="debug/recent-events", auth_level=func.AuthLevel.ANONYMOUS)
def recent_events(req: func.HttpRequest) -> func.HttpResponse:
    """Show recently processed events for debugging"""
    try:
        from src.utils.deduplication import message_deduplicator
        from src.utils.early_dedup import get_stats as get_early_stats
        
        # Get recent events from both deduplicators
        regular_stats = message_deduplicator.get_stats()
        early_stats = get_early_stats()
        recent_messages = list(message_deduplicator.processed_messages.keys())[-10:]  # Last 10 messages
        
        debug_info = {
            "recent_message_ids": recent_messages,
            "total_processed": len(message_deduplicator.processed_messages),
            "regular_deduplication_stats": regular_stats,
            "early_deduplication_stats": early_stats,
            "queue_status": "Active",
            "timestamp": str(__import__('datetime').datetime.utcnow())
        }
        
        return func.HttpResponse(
            json.dumps(debug_info, indent=2),
            mimetype="application/json"
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
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
