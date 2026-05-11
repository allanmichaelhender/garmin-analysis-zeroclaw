# Garmin MCP Server

A Model Context Protocol (MCP) server that exposes Garmin Connect fitness data as tools for ZeroClaw agent integration.

## Features

- **8 MCP Tools**: Get activities, details, heart rate data, analysis, workout metadata, interval detection, and more
- **FastAPI + FastMCP**: Modern Python web framework with MCP protocol support
- **PostgreSQL Database**: Stores activities, heart rate data, workout metadata, and activity intervals
- **ZeroClaw Integration**: HTTP transport for agent runtime
- **Docker Deployment**: Containerized with PostgreSQL and pgAdmin
- **Modular Architecture**: Tools organized by category (Garmin, Workout, Analysis)

## Architecture

```
garmin-analysis/
├── backend/          # MCP server (FastAPI + FastMCP)
│   ├── app/
│   │   ├── core/     # Database and configuration
│   │   ├── mcp/      # MCP server and tools (modular)
│   │   │   ├── garmin/    # Garmin-related tools
│   │   │   ├── workout/   # Workout metadata tools
│   │   │   └── analysis/  # Analysis tools
│   │   ├── clients/  # Garmin Connect API client
│   │   ├── models/   # SQLAlchemy models
│   │   └── services/ # Changepoint detection service
│   ├── alembic/      # Database migrations
│   └── scripts/      # Data ingestion scripts
├── zeroclaw/         # ZeroClaw agent runtime
├── zeroclaw-web/     # ZeroClaw source code (for reference)
└── docker-compose.yml # Orchestrates all services
```

## MCP Tools

### Garmin Tools
1. `garmin__echo` - Test tool for MCP connectivity
2. `garmin__get_garmin_data` - Retrieve Garmin data with filters
3. `garmin__analyze_activity` - Analyze activity performance
4. `garmin__get_recent_activities` - Get recent Garmin activities
5. `garmin__sync_garmin_activities` - Sync new activities from Garmin Connect

### Workout Tools
6. `garmin__get_pending_metadata` - Get activities needing workout metadata
7. `garmin__save_workout_metadata` - Save workout metadata (RPE, feeling, session structure)

### Analysis Tools
8. `garmin__detect_activity_intervals` - Detect workout intervals using changepoint detection

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env with your PostgreSQL and Garmin credentials, and ZeroClaw API keys
```

**⚠️ IMPORTANT - Environment Variables in ZeroClaw Config**

ZeroClaw's `config.toml` cannot directly parse environment variables using `${VAR}` syntax (TOML doesn't support this). To use environment variables for sensitive data like API keys and bot tokens:

1. Store them in `zeroclaw/.env`:

   ```bash
   ANTHROPIC_API_KEY=your_key_here
   DISCORD_BOT_TOKEN=your_token_here
   ```

2. Reference them in `config.toml` using `${VARIABLE}` placeholders:

   ```toml
   [providers.models.anthropic]
   api_key = "${ANTHROPIC_API_KEY}"

   [channels.discord]
   bot_token = "${DISCORD_BOT_TOKEN}"
   ```

3. The `entrypoint.sh` script (in the Dockerfile) automatically:
   - Loads your `.env` file
   - Substitutes all `${VARIABLE}` placeholders with real values using `envsubst`
   - Generates the final `config.toml` before ZeroClaw starts

This keeps secrets out of version control and allows Docker environment variables to work seamlessly.

### 2. Start Services

```bash
docker compose up -d --build
```

### 3. Verify MCP Connection

**IMPORTANT**: Follow the [MCP Connection Setup Guide](mcp-connection-setup.md) to ensure proper MCP integration.

Check that ZeroClaw can connect to the MCP server:

```bash
# Check backend health
curl http://localhost:8000/health

# Check backend logs for tool execution
docker compose logs backend -f

# Check ZeroClaw MCP connection
docker compose logs zeroclaw | grep -i "mcp\|tool"

# Expected output:
# MCP server `garmin` connected — 4 tool(s) available
```

### 4. Configure Tool Auto-Approval

**CRITICAL**: Add Garmin MCP tools to ZeroClaw's auto-approve list to enable execution:

```toml
# In zeroclaw/config.toml
[autonomy]
auto_approve = [
  "garmin__echo",
  "garmin__get_recent_activities",
  "garmin__get_garmin_data",
  "garmin__analyze_activity",
  "garmin__detect_activity_intervals"
]
```

### 5. Test MCP Tools

Test the MCP tools through ZeroClaw's web interface at `http://localhost:8080` or via webhook:

```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "Use the garmin__echo tool to say hello"}'
```

## Troubleshooting

If MCP connections fail, see the [MCP Connection Setup Guide](mcp-connection-setup.md) for common issues and solutions.

**Related Guides:**

- [MCP Connection Setup Guide](mcp-connection-setup.md) - Detailed MCP setup and troubleshooting
- [ZeroClaw Integration Guide](zeroclaw-integration.md) - ZeroClaw setup and configuration
- [MCP Server Implementation Plan](mcp-server-implementation-plan.md) - Development roadmap

```bash
docker-compose up -d --build
```

This starts both the backend (MCP server) and ZeroClaw.

### 3. Database Setup

The database is automatically initialized on startup using Alembic migrations. PostgreSQL is hosted on Neon and accessible via pgAdmin at http://localhost:5050.

```bash
# Test database connection
curl http://localhost:8000/health
```

### 4. Data Ingestion

```bash
# Sync activities from Garmin Connect (via MCP tool)
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "Use the sync_garmin_activities tool with limit=20"}'

# Or run ingestion script directly
docker compose exec backend python scripts/ingest_activities.py
```

### 5. ZeroClaw Integration

ZeroClaw is automatically configured to connect to the backend. See `zeroclaw-integration.md` for detailed setup.

### 6. Test MCP Server

```bash
# Test health check
curl http://localhost:8000/health

# MCP tools are available at /mcp endpoint
curl http://localhost:8000/mcp
```

### 7. Test ZeroClaw

```bash
# Access ZeroClaw CLI
docker-compose exec zeroclaw zeroclaw agent
```

## ZeroClaw Integration

ZeroClaw is configured in `zeroclaw/config.toml` to connect to the backend via HTTP transport:

```toml
[mcp_servers.garmin]
transport = "http"
url = "http://backend:8000/mcp"
```

See `zeroclaw-integration.md` for detailed setup instructions.

## Database Schema

- **activities**: Garmin activity data with full metrics
- **heart_rate_data**: Heart rate time series data
- **activity_intervals**: Changepoint detection results for workout intervals
- **workout_metadata**: User-provided workout metadata (RPE, feeling, session structure)

## Development

```bash
# Local development
cd backend
pip install -r requirements.txt
uvicorn app.mcp_server:app --reload

# View logs with tool execution traces
docker compose logs -f backend
```

## Monitoring

```bash
# View container logs
docker-compose logs -f mcp-server

# Test server health
curl http://localhost:8000/health
```

## Environment Variables

- `DATABASE_URL`: Neon PostgreSQL connection string
- `GARMIN_EMAIL`: Garmin Connect email
- `GARMIN_PASSWORD`: Garmin Connect password
- `LOG_LEVEL`: Logging level (default INFO)

## Changepoint Detection

The system includes changepoint detection to automatically segment workouts into intervals based on heart rate patterns:

- **Algorithm**: Uses ruptures library with PELT (Pruned Exact Linear Time) algorithm
- **Detection**: Identifies statistical changes in heart rate data
- **Parameters**: Adjustable penalty value (higher = fewer intervals, lower = more sensitive)
- **Storage**: Detected intervals stored in `activity_intervals` table with HR statistics
- **Usage**: Call `detect_activity_intervals` MCP tool with activity ID and penalty parameter

## Troubleshooting

1. **Database connection fails**: Check DATABASE_URL in .env and Neon status
2. **Garmin auth fails**: Verify GARMIN_EMAIL and GARMIN_PASSWORD in .env
3. **Docker issues**: Check `docker compose logs backend`
4. **No activities**: Run sync_garmin_activities MCP tool or ingestion script
5. **MCP tools not found**: Check [MCP Connection Setup Guide](mcp-connection-setup.md)

## License

MIT
