# Slack Bot API Testing Collection

This Bruno collection contains API requests for testing all endpoints of the Slack Bot application.

## Setup

1. Install Bruno: https://www.usebruno.com/
2. Open Bruno and load this collection
3. Select appropriate environment (local or azure)

## Environments

### Local Environment
- **URL**: `http://localhost:7071`
- **Usage**: Testing with Azure Functions running locally
- **Setup**: Run `func start` in the project directory

### Azure Environment
- **URL**: `https://fa-slack-core-dev-arf7axhva9brcufk.westus2-01.azurewebsites.net`
- **Usage**: Testing against deployed Azure Functions
- **Setup**: Ensure Function App is deployed and running

## Request Categories

### Debug Endpoints
- **Test Settings**: Environment variables and configuration
- **Dedup Stats**: Message deduplication statistics
- **Test Plugins**: Plugin pattern matching tests
- **Recent Events**: Recent Slack events processed

### Slack API Endpoints
- **Slack Events**: Receives Slack webhook events
- **Slack Commands**: Handles slash commands

### Plugin Tests
Individual tests for each plugin:
- **Ping Plugin**: `ping` command
- **Incident Plugin**: `incident <id>` command (regex)
- **Help Plugin**: `help` command
- **Status Plugin**: `status` command
- **No Match Test**: Tests unmatched patterns

### Slack Events
Simulated Slack events:
- **App Mention - Incident**: `@bot incident 456`
- **App Mention - Help**: `@bot help`

### Slash Commands
Direct slash command tests:
- **Hello Command**: `/hello [message]`
- **Info Command**: `/info`
- **Help Command**: `/help`

### Basic Tests
- **Health Check**: Comprehensive health monitoring endpoint

## Usage Tips

### Environment Switching
1. Click on the environment dropdown (top right)
2. Select "local" for local testing
3. Select "azure" for production testing

### Local Testing
1. Start Azure Functions: `func start`
2. Switch to "local" environment
3. Test debug endpoints first to verify setup

### Production Testing
1. Ensure Function App is deployed
2. Switch to "azure" environment  
3. Test basic endpoints first

### Plugin Testing Workflow
1. Use "Test Plugins" requests to verify pattern matching
2. Use "Slack Events" requests to test full event flow
3. Check "Dedup Stats" to monitor deduplication
4. Use "Recent Events" to see processing history

## Request Details

### Authentication
- Most endpoints don't require authentication for testing
- Slack webhook endpoints include mock signatures
- Real Slack requests would have proper signatures

### Headers
- **Slack Events**: Require `X-Slack-Signature` and `X-Slack-Request-Timestamp`
- **Slack Commands**: Use `application/x-www-form-urlencoded`
- **Debug Endpoints**: Use `application/json`

### Expected Responses

#### Debug Endpoints
- **200 OK**: Successful responses with JSON data
- **500 Error**: Configuration or processing errors

#### Slack Endpoints
- **200 OK**: Event processed successfully
- **400 Bad Request**: Invalid request format
- **401 Unauthorized**: Invalid signature (in production)

## Troubleshooting

### Local Environment Issues
- Ensure `func start` is running
- Check port 7071 is available
- Verify all environment variables are set

### Azure Environment Issues
- Check Function App status in Azure portal
- Verify deployment completed successfully
- Review Function App logs for errors

### Plugin Issues
- Use "Test Plugins" to verify pattern matching
- Check plugins.yaml configuration
- Review plugin implementation for errors

### Event Processing Issues
- Check "Dedup Stats" for duplicate handling
- Review "Recent Events" for processing history
- Verify Service Bus connection in production

## Development Workflow

1. **Local Development**:
   - Use local environment
   - Test debug endpoints
   - Verify plugin changes

2. **Deployment Testing**:
   - Deploy to Azure Functions
   - Switch to azure environment
   - Test full event flow

3. **Plugin Development**:
   - Test patterns with "Test Plugins"
   - Simulate events with "Slack Events"
   - Verify responses and behavior

4. **Monitoring**:
   - Check deduplication stats
   - Monitor recent events
   - Review error responses
