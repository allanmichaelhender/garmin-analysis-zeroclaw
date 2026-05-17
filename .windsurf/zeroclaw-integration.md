# ZeroClaw Integration Guide

## Overview

This guide covers integrating the Garmin MCP Server with ZeroClaw, a self-hosted AI agent runtime that provides advanced agent controls, multiple channel support, and privacy-first execution.

## What is ZeroClaw?

ZeroClaw is a Rust-based AI agent runtime that:

- **Acts as an MCP Client**: Connects to external MCP servers via HTTP transport
- **Supports 30+ Channels**: Discord, Telegram, Matrix, email, CLI, webhooks, etc.
- **Provider-Agnostic**: Works with Anthropic, OpenAI, Ollama, and 20+ other LLM providers
- **Security-First**: Sandbox execution, approval gates, tool receipts
- **Privacy-First**: 100% local execution when using Ollama
- **Advanced Controls**: SOP engine, cron jobs, hardware support

## Prerequisites

- Garmin MCP Server running
- LLM provider account (Anthropic, OpenAI, or Ollama for local)

## Installation Options

### Option 1: Docker (Recommended)

The easiest way to run ZeroClaw is with Docker, which includes the Garmin MCP server in the same stack.

```bash
cd zeroclaw
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d --build
```

This will start both ZeroClaw and the Garmin MCP server together.

### Option 2: Native Installation

```bash
curl -fsSL https://raw.githubusercontent.com/zeroclaw-labs/zeroclaw/master/install.sh | bash
```

Or clone and install:

```bash
git clone https://github.com/zeroclaw-labs/zeroclaw.git
cd zeroclaw
./install.sh
```

## MCP Configuration

### ZeroClaw MCP Client Setup

ZeroClaw connects to MCP servers via HTTP transport. Configure the connection in `zeroclaw/config.toml`:

```toml
[mcp]
enabled = true
deferred_loading = false

[[mcp.servers]]
name = "garmin"
transport = "http"
url = "http://backend:8000/mcp"  # Must match FastMCP server mount path
```

**⚠️ CRITICAL**: The URL must exactly match the path where the FastMCP HTTP app is mounted in the server. See [MCP Connection Setup Guide](../mcp-connection-setup.md) for details.

### Managing Environment Variables in config.toml

**Important**: TOML files cannot natively parse `${VARIABLE}` syntax—this is a shell/Docker feature, not a TOML feature.

**Workaround**: Use `entrypoint.sh` to substitute variables before ZeroClaw starts:

1. Store sensitive values in `zeroclaw/.env`:

   ```
   ANTHROPIC_API_KEY=sk-...
   DISCORD_BOT_TOKEN=...
   ```

2. Use placeholders in `zeroclaw/config.toml`:

   ```toml
   [providers.models.anthropic]
   api_key = "${ANTHROPIC_API_KEY}"

   [channels.discord]
   bot_token = "${DISCORD_BOT_TOKEN}"
   ```

3. The Docker `ENTRYPOINT` (entrypoint.sh) automatically:
   - Sources `/root/.zeroclaw/.env` (mounted from your local `zeroclaw/.env`)
   - Runs `envsubst` to replace all `${VAR}` with actual values
   - Generates the final processed `config.toml`
   - Starts ZeroClaw with the populated config

**Why this works**:

- `envsubst` is a Unix utility that replaces shell variables in files
- We mount your `zeroclaw/` directory as a volume, so the `.env` file is available inside the container
- The entrypoint script runs before ZeroClaw starts, ensuring all values are substituted

### Verifying MCP Connection

After starting the services, verify the MCP connection:

```bash
# Check backend health
curl http://localhost:8000/health

# Check backend logs for tool execution
docker compose logs backend -f

# Check ZeroClaw logs for MCP connection
docker compose logs zeroclaw | grep -i "mcp\|tool"

# Expected successful output:
# backend  | 🔵 REQUEST: POST /mcp
# backend  | 🔵 REQUEST BODY: {"jsonrpc":"2.0",...}
# backend  | 🔧 TOOL CALL: echo(message='hello')
# backend  | 🔧 TOOL RESULT: echo -> 'Echo: hello'
# backend  | 🟢 RESPONSE: 200
# zeroclaw  | MCP server `garmin` connected — 9 tool(s) available
# zeroclaw  | Gateway MCP: 9 tool(s) registered from 1 server(s)
```

### Testing MCP Tools

#### Via Web Interface

1. Open ZeroClaw web UI: `http://localhost:8080`
2. Use the chat interface to test tools
3. Try: _"Use the echo tool to say hello world"_

#### Via Webhook API

```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "Test the garmin__echo tool with hello world"}'
```

**Note**: Tool names are prefixed with the MCP server name (e.g., `garmin__echo`).

#### Auto-Approval Configuration

**CRITICAL**: MCP tools require explicit approval by default. Add Garmin tools to the auto-approve list:

```toml
[autonomy]
auto_approve = [
  "file_read", "memory_recall", "web_search_tool", "web_fetch",
  "calculator", "glob_search", "content_search", "image_info",
  "weather", "browser", "browser_open",
  "garmin__echo",                      # ✅ Garmin MCP tools
  "garmin__get_recent_activities",     # ✅
  "garmin__get_garmin_data",           # ✅
  "garmin__analyze_activity",          # ✅
  "garmin__get_hr_10sec_averages",     # ✅
  "garmin__sync_garmin_activities",    # ✅
  "garmin__get_pending_metadata",      # ✅
  "garmin__save_workout_metadata",     # ✅
  "garmin__detect_activity_intervals"   # ✅
]
```

Without this configuration, MCP tools will be **denied execution** even when properly connected.

## Security Considerations

ZeroClaw implements security controls for tool execution:

- **Approval Gates**: Tools require user approval by default
- **Sandbox Execution**: Tools run in isolated environments
- **Audit Logging**: All tool executions are logged

### Disabling Approvals (For Development)

For development/testing, you can disable tool approval requirements:

```toml
[security.otp]
gated_actions = []  # Remove default security gates
```

**⚠️ WARNING**: Only disable approvals in development environments.

## Troubleshooting MCP Issues

### Common Problems

1. **"0 tool(s) registered"**
   - Check ZeroClaw config URL matches server mount path
   - Verify backend service is healthy: `curl http://localhost:8000/health`
   - Check backend logs: `docker compose logs backend`

2. **"Tool execution denied" / "MCP tools not working"**
   - **SOLUTION**: MCP tools require explicit approval. Add them to `[autonomy].auto_approve` list
   - This is the most common issue - MCP tools are connected but blocked by security
   - Example config:
     ```toml
     [autonomy]
     auto_approve = ["garmin__echo", "garmin__get_recent_activities", ...]
     ```

3. **Connection refused**
   - Ensure `depends_on` is set in docker-compose.yml
   - Use service names (`backend:8000`) not `localhost:8000` in configs

### Debug Commands

```bash
# Check all service health
docker compose ps

# View detailed logs
docker compose logs -f

# Test backend connectivity from ZeroClaw container
docker exec zeroclaw curl -v http://backend:8000/mcp

# Check MCP server directly
curl -v http://localhost:8000/mcp

# View backend logs with tool execution traces
docker compose logs -f backend
```

## Advanced Configuration

### Multiple MCP Servers

ZeroClaw can connect to multiple MCP servers:

```toml
[[mcp.servers]]
name = "garmin"
transport = "http"
url = "http://backend:8000/mcp"

[[mcp.servers]]
name = "weather"
transport = "http"
url = "http://weather-service:8000/mcp"
```

### Environment Variables

Pass API keys and configuration via environment:

```bash
# In docker-compose.yml
environment:
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  - OPENAI_API_KEY=${OPENAI_API_KEY}
```

### Custom Providers

ZeroClaw supports custom LLM providers. Configure in `config.toml`:

```toml
[providers]
fallback = "anthropic"

[providers.models.anthropic]
model = "claude-sonnet-4-6"
api_key = "${ANTHROPIC_API_KEY}"
```

## Related Documentation

- [MCP Connection Setup Guide](../mcp-connection-setup.md) - Detailed MCP setup and troubleshooting
- [README](../readme.md) - Project overview and quickstart
- [MCP Server Implementation Plan](../mcp-server-implementation-plan.md) - Development roadmap

### Initialize ZeroClaw (Native Only)

```bash
zeroclaw onboard
```

This wizard will guide you through:

- Selecting an LLM provider
- Configuring API keys
- Setting up initial channels

## Configuration

### Docker Configuration

With Docker, configuration is handled via `zeroclaw/config.toml` and environment variables:

**Edit `zeroclaw/config.toml`:**

```toml
[mcp_servers.garmin]
transport = "http"
url = "http://backend:8000/mcp"
```

**Note**: The service name in docker-compose.yml is `backend`, not `mcp-server`.

**Edit `zeroclaw/.env`:**

```bash
ANTHROPIC_API_KEY=your_key_here
# or OPENAI_API_KEY=your_key_here
```

### Native Configuration

Edit `~/.zeroclaw/config.toml` to add the Garmin MCP server:

```toml
[mcp_servers.garmin]
transport = "http"
url = "http://localhost:8000/mcp"
```

### LLM Provider Configuration

Choose your provider in the config file:

**Anthropic:**

```toml
default_provider = "anthropic"
api_key = "${ANTHROPIC_API_KEY}"

[providers.models.anthropic]
model = "claude-haiku-4-5@20251001"
```

**OpenAI:**

```toml
[providers.models.openai]
provider = "openai"
model = "gpt-4-turbo"
api_key = "${OPENAI_API_KEY}"
```

**Ollama (Local):**

```toml
[providers.models.ollama]
provider = "ollama"
model = "llama3:70b"
base_url = "http://host.docker.internal:11434"
```

### Channel Configuration

Configure your preferred channels in the config file:

**CLI Channel:**

```toml
channels.cli = true
```

**Discord Channel:**

```toml
[channels.discord]
enabled = true
token = "${DISCORD_BOT_TOKEN}"
```

**Telegram Channel:**

```toml
[channels.telegram]
enabled = true
token = "${TELEGRAM_BOT_TOKEN}"
```

## Testing

### Docker Testing

```bash
# Start ZeroClaw and MCP server
cd zeroclaw
docker-compose up -d

# View logs
docker-compose logs -f zeroclaw

# Access ZeroClaw CLI
docker-compose exec zeroclaw zeroclaw agent
```

### Native Testing

```bash
# Start ZeroClaw
zeroclaw agent
```

This starts the interactive CLI channel.

### Test MCP Connection

In the ZeroClaw CLI, try:

```
List my recent activities
```

ZeroClaw should:

1. Recognize the intent
2. Call the `get_recent_activities` MCP tool
3. Display the results

### Test Other Tools

```
Show me details for activity 12345
What's my heart rate data for my last run?
Compare my last 5 runs
```

## Advanced Features

### SOP Engine

Create Standard Operating Procedures (SOPs) in `~/.zeroclaw/config.toml`:

```toml
[sops.daily_analysis]
trigger = "cron"
schedule = "0 8 * * *"  # 8 AM daily
steps = [
    {tool = "get_recent_activities", args = {limit = 10, activity_type = "running"}},
    {tool = "get_training_load", args = {days = 7}}
]
approval = "medium"
```

### Approval Gates

Configure approval levels in `~/.zeroclaw/config.toml`:

```toml
[security]
autonomy = "supervised"
approval_medium = true  # Require approval for medium-risk ops
approval_high = true   # Block high-risk ops
```

### Tool Receipts

Enable cryptographic receipts for audit trails:

```toml
[security]
tool_receipts = true
```

### YOLO Mode (Development Only)

Disable all safety checks for trusted environments:

```bash
zeroclaw agent --yolo
```

## Channel-Specific Setup

### Discord

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot user
3. Invite the bot to your server
4. Copy the bot token
5. Configure in `~/.zeroclaw/config.toml`

### Telegram

1. Create a bot via @BotFather on Telegram
2. Copy the API token
3. Configure in `~/.zeroclaw/config.toml`

### CLI

The CLI channel is enabled by default after installation.

## Privacy Considerations

**With Ollama (Local LLM):**

- 100% local execution
- No data leaves your machine
- Maximum privacy

**With Cloud LLMs (Anthropic/OpenAI):**

- Tool calls and responses sent to LLM provider
- Garmin data processed locally before sending summaries
- Check provider privacy policies

## Troubleshooting

### MCP Connection Fails

1. Verify MCP server is running: `curl http://localhost:8000/health`
2. Check ZeroClaw config: `~/.zeroclaw/config.toml`
3. Check ZeroClaw logs: `zeroclaw logs`

### Tools Not Discovered

1. Verify MCP endpoint: `curl http://localhost:8000/mcp`
2. Check MCP server logs: `docker-compose logs mcp-server`
3. Restart ZeroClaw: `zeroclaw service restart`

### LLM Provider Issues

1. Verify API key in config
2. Check provider status
3. Test with CLI: `zeroclaw agent --provider ollama`

## Next Steps

- Configure additional channels (Discord, Telegram)
- Set up SOPs for automated tasks
- Configure approval gates for safety
- Explore hardware integration (GPIO, I2C, SPI)
- Set up ZeroClaw as a background service

## Resources

- [ZeroClaw GitHub](https://github.com/zeroclaw-labs/zeroclaw)
- [ZeroClaw Documentation](https://github.com/zeroclaw-labs/zeroclaw/blob/master/docs/book/src/README.md)
- [ZeroClaw Discord](https://discord.com/invite/wDshRVqRjx)
- **Local ZeroClaw Repository**: The `zeroclaw-web/` directory contains the full ZeroClaw source code for reference and customization
