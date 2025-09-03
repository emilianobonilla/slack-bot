# Slack Bot Setup Guide

This guide will help you configure your Slack bot from scratch to get it running in both development and production environments.

## Prerequisites

- Slack account with permissions to create apps
- Python 3.8+ installed
- Azure account (optional, for production)

## Step 1: Create the Slack App

### 1.1 Access the Slack API Portal

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Select "From scratch"
4. Give your app a name (e.g., "My Slack Bot")
5. Select the workspace where you want to install the bot

### 1.2 Configure Bot Permissions

1. In your app page, go to **"OAuth & Permissions"** in the sidebar
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add the following scopes:

**Required scopes:**
- `app_mentions:read` - To respond when the bot is mentioned
- `channels:history` - To read messages in channels
- `chat:write` - To send messages
- `commands` - To handle slash commands
- `im:history` - To read direct messages
- `im:write` - To send direct messages
- `reactions:read` - To read reactions
- `users:read` - To get user information

**Optional scopes (as needed):**
- `channels:read` - To get channel information
- `groups:history` - To read messages in private groups
- `groups:write` - To send messages in private groups
- `team:read` - To get team information

### 1.3 Install the App in your Workspace

1. After adding scopes, scroll up on the same page
2. Click **"Install to Workspace"**
3. Authorize the application
4. **IMPORTANT!** Copy the **"Bot User OAuth Token"** that starts with `xoxb-`

### 1.4 Get the Signing Secret

1. Go to **"Basic Information"** in the sidebar
2. In the **"App Credentials"** section, copy the **"Signing Secret"**

### 1.5 Configure Socket Mode (For Development)

1. Go to **"Socket Mode"** in the sidebar
2. Enable **"Enable Socket Mode"**
3. Create an app-level token:
   - Click "Generate Token and Scopes"
   - Name: "socket-mode-token"
   - Scopes: `connections:write`
4. **IMPORTANT!** Copy the **"App-Level Token"** that starts with `xapp-`

### 1.6 Configure Event Subscriptions

1. Go to **"Event Subscriptions"** in the sidebar
2. Enable **"Enable Events"**
3. If using Socket Mode, no URL is needed
4. In **"Subscribe to bot events"**, add:
   - `app_mention` - When the bot is mentioned
   - `message.im` - Direct messages
   - `reaction_added` - Reactions added
   - `team_join` - New members

### 1.7 Configure Slash Commands (Optional)

1. Go to **"Slash Commands"** in the sidebar
2. Click **"Create New Command"**
3. Configure the following commands:

**Command /hello:**
- Command: `/hello`
- Request URL: (empty if using Socket Mode)
- Short Description: "Greet the bot"
- Usage Hint: `[optional message]`

**Command /info:**
- Command: `/info`
- Request URL: (empty if using Socket Mode)
- Short Description: "Bot information"

**Command /help:**
- Command: `/help`
- Request URL: (empty if using Socket Mode)
- Short Description: "Bot help"

## Step 2: Configure Development Environment

### 2.1 Configure Environment Variables

1. Copy the template file:
```bash
cp .env.template .env
```

2. Edit the `.env` file with your tokens:
```bash
# Replace with your actual tokens
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_SIGNING_SECRET=your-actual-signing-secret
SLACK_APP_TOKEN=xapp-your-actual-app-token
SLACK_SOCKET_MODE=true
```

### 2.2 Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2.3 Test the Configuration

```bash
# Run the bot in development mode
python -m src.app

# Or directly:
python src/app.py
```

If everything is configured correctly, you'll see:
```
Starting Slack bot app_name=SlackBot version=1.0.0
Running in Socket Mode (development)
Bolt app is running!
```

## Step 3: Test the Bot

### 3.1 Basic Tests

1. **Mention the bot:** In any channel, type `@YourBotName hello`
2. **Direct message:** Send a DM to the bot with "hello"
3. **Slash commands:** Try `/hello`, `/info`, `/help`

### 3.2 Verify Logs

The bot will show structured logs in the console:
```
Processing Slack event event_type=app_mention user_id=U1234567
Responded to app mention user_id=U1234567 channel_id=C1234567
```

## Step 4: Production Configuration (Azure Functions)

### 4.1 Prepare Azure Functions

1. Install Azure Functions Core Tools:
```bash
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

2. Copy the local configuration:
```bash
cp local.settings.json.template local.settings.json
```

3. Edit `local.settings.json` with your actual tokens

### 4.2 Test Locally with Azure Functions

```bash
func start
```

### 4.3 Configure for HTTP Mode (Production)

1. In your Slack app, go to **"Socket Mode"**
2. **Disable Socket Mode**
3. Go to **"Event Subscriptions"**
4. Configure the Request URL: `https://your-function-app.azurewebsites.net/api/slack/events`
5. Configure Slash Command URLs: `https://your-function-app.azurewebsites.net/api/slack/commands`

### 4.4 Deploy to Azure

```bash
func azure functionapp publish <your-function-app-name>
```

### 4.5 Configure Azure Service Bus (Required for Production)

1. Create an Azure Service Bus namespace
2. Create a queue named "slack-events"
3. Get the connection string and add it to your Azure Function environment variables:
   - `SERVICE_BUS_CONNECTION_STRING`

## Troubleshooting

### Error: "Configuration validation failed"

Verify that all environment variables are configured correctly:
```bash
python -c "from src.config import validate_configuration; print(validate_configuration())"
```

### Error: "Failed to start Slack bot"

1. Verify that tokens are correct
2. Ensure Socket Mode is enabled (development)
3. Check that scopes are configured

### Bot doesn't respond to mentions

1. Verify the bot is in the channel
2. Check event subscriptions in Slack
3. Confirm that `app_mentions:read` scope is added
4. Check Azure Function logs for errors

### Slash commands don't work

1. Verify commands are created in Slack
2. If using HTTP mode, configure URLs correctly
3. Check that `commands` scope is added

### Duplicate messages

1. Check deduplication statistics at `/api/debug/dedup-stats`
2. Verify Service Bus duplicate detection is enabled
3. Review Azure Function logs for processing issues

## Development Commands

```bash
# Run the bot
python -m src.app

# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Code formatting
black src/ plugins/
isort src/ plugins/

# Linting
flake8 src/ plugins/

# Azure Functions local
func start
```

## Architecture Overview

The bot uses an asynchronous architecture:

1. **Immediate Response**: Bot acknowledges Slack events within 3 seconds
2. **Queue Processing**: Events are queued in Azure Service Bus for processing
3. **Plugin System**: Modular plugins handle different command types
4. **Deduplication**: Built-in mechanisms prevent duplicate responses

## Security

- **Never** commit real tokens to the repository
- Use environment variables for all secrets
- In production, use Azure Key Vault or similar
- Always verify Slack signatures
- Use HTTPS for all endpoints

## Plugin System

The bot supports a modular plugin architecture:

- Plugins are configured in `plugins.yaml`
- Each plugin extends the `BasePlugin` class
- Supports regex and string pattern matching
- Can respond in channels, DMs, or specific channels

### Available Plugins

- **ping** - Simple connectivity test
- **incident** - Retrieve incident information by ID
- **help** - Show available commands
- **status** - Display bot health metrics

## Monitoring

The bot includes debugging endpoints:
- `/api/debug/env` - Environment variables
- `/api/debug/plugins` - Test plugin matching
- `/api/debug/dedup-stats` - Deduplication statistics

## Additional Resources

- [Slack API Documentation](https://api.slack.com/)
- [Slack Bolt Framework](https://slack.dev/bolt-python/tutorial/getting-started)
- [Azure Functions Python Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Azure Service Bus Documentation](https://docs.microsoft.com/en-us/azure/service-bus-messaging/)

---

Your Slack bot is ready!
