# MCP Server Implementation Plan

Implementation plan for building a Model Context Protocol (MCP) server that exposes Garmin fitness data as tools for ZeroClaw agent integration.

**Related Guides:**

- `readme.md` - Project overview and quickstart
- `mcp-connection-setup.md` - **CRITICAL**: MCP connection setup and troubleshooting
- `zeroclaw-integration.md` - ZeroClaw setup and configuration

---

## Phase 1: Project Setup & Infrastructure ✅

### 1.1 Create Project Structure

- [x] Create root directory `backend/`
- [x] Create directory structure:
  ```
  backend/
  ├── app/
  │   ├── core/       # Database and configuration
  │   ├── mcp/        # MCP server and tools (modular)
  │   │   ├── garmin/    # Garmin-related tools
  │   │   ├── workout/   # Workout metadata tools
  │   │   └── analysis/  # Analysis tools
  │   ├── clients/
  │   ├── models/
  │   └── services/
  ├── alembic/
  │   └── versions/
  └── scripts/
  ```

### 1.2 Create Configuration Files

- [x] Create `docker-compose.yml` in root with backend and zeroclaw services
- [x] Create `backend/Dockerfile` for FastAPI application with FastMCP
- [x] Create `backend/requirements.txt` with all dependencies
- [x] Create `.env.example` with environment variable templates
- [x] Create `.gitignore` for sensitive files

### 1.3 Create Python Package Files

- [x] Create `backend/app/__init__.py`
- [x] Create `backend/app/clients/__init__.py`
- [x] Create `backend/app/tools/__init__.py`
- [x] Create `backend/app/models/__init__.py`
- [x] Create `backend/app/core/config.py`
- [x] Create `backend/app/core/database.py`

### 1.4 Initialize Database

- [x] Create `backend/app/core/database.py` with SQLAlchemy models
- [x] Set up Alembic for database migrations
- [x] Create initial migration `backend/alembic/versions/20260510_2100_initial_schema.py`
- [x] Test PostgreSQL connectivity (Neon)

## Phase 2: MCP Server Implementation ✅

### 2.1 FastMCP Server Setup

- [x] Install FastMCP v3.2.4
- [x] Create single FastMCP instance (avoid multiple instances!)
- [x] Configure HTTP transport for ZeroClaw
- [x] Set up proper FastAPI lifespan management
- [x] Mount MCP app at `/mcp` endpoint
- [x] Add health check endpoint
- [x] Add logging middleware for request/response tracking
- [x] Add tool-level logging for debugging

### 2.2 MCP Tool Development

- [x] Create Garmin tools (app/mcp/garmin/tools.py):
  - `echo` - Test tool for debugging
  - `sync_garmin_activities` - Sync activities from Garmin Connect
- [x] Removed workout and analysis tools (simplified to core sync + echo only)
- [x] Add logging to all tool functions for debugging
- [x] Create main MCP orchestrator in app/mcp/mcp.py
- [x] Fix app.py to import from mcp.mcp instead of monolithic mcp_tools.py

### 2.3 Garmin API Integration

- [x] Create Garmin Connect API client in `backend/app/clients/garmin.py`
- [x] Implement authentication (email/password)
- [x] Implement `get_activities()` method with pagination
- [x] Implement `get_activity_details()` method
- [x] Implement `get_activity_samples()` method for heart rate time series
- [x] Handle API rate limits and error responses
- [x] Add data validation and error handling

## Phase 3: ZeroClaw Integration ✅

### 3.1 MCP Client Configuration

- [x] Configure ZeroClaw to connect to MCP server
- [x] Set correct HTTP transport URL: `http://backend:8000/mcp`
- [x] Verify tool registration in ZeroClaw logs
- [x] Test tool execution through ZeroClaw UI/webhook

### 3.2 Security & Permissions

- [x] Understand ZeroClaw approval gates for tool execution
- [x] Configure appropriate security settings for production (auto-approve list)
- [x] Implement proper error handling for denied requests

## Phase 4: Data Storage & Processing

### 4.1 Database Schema

- [x] Design PostgreSQL schema for:
  - `activities` - Activity metadata and summaries
  - `heart_rate_data` - Time-series heart rate data
  - `activity_intervals` - Changepoint detection results
  - `workout_metadata` - User-provided workout metadata (RPE, feeling, session structure)
- [x] Create SQLAlchemy models
- [x] Set up database initialization with Alembic

### 4.2 Data Ingestion Pipeline

- [x] Create data ingestion scripts in `backend/scripts/`
- [x] Implement Garmin activity ingestion with pagination
- [x] Add data validation and deduplication
- [x] Implement scheduled data sync from Garmin (via MCP tool)
- [x] Handle incremental updates (check for existing activities)

### 4.3 LLM Integration

- [ ] Integrate LLM for activity analysis and summaries
- [ ] Store LLM-generated insights in database
- [ ] Implement feedback loop for improving summaries
- [ ] Add llm_summaries table when implemented

## Phase 5: Testing & Deployment

### 5.1 Testing

- [x] Unit tests for MCP tools
- [x] Integration tests for MCP server
- [x] End-to-end tests with ZeroClaw
- [ ] Load testing for concurrent requests

### 5.2 Deployment

- [x] Docker containerization
- [x] Docker Compose orchestration
- [x] pgAdmin service for database management
- [ ] Production deployment scripts
- [ ] Monitoring and logging setup

## Lessons Learned (From MCP Connection Issues)

### Critical MCP Setup Mistakes to Avoid

1. **Multiple FastMCP Instances**: FastMCP v3.x doesn't support multiple instances. Always use one instance per server.

2. **Missing Python Package Files**: Always add `__init__.py` files to make directories proper Python packages.

3. **Incorrect Transport URLs**: ZeroClaw HTTP transport must connect to the exact path where `http_app` is mounted (`/mcp`).

4. **Deprecated API Usage**: Don't use `prefix` parameter in FastMCP constructor - it's deprecated in v3.x.

5. **Service Dependencies**: Use `depends_on` in docker-compose.yml to ensure backend starts before ZeroClaw.

6. **Container Networking**: Use service names (`backend:8000`) in configs, not `localhost:8000`.

7. **Wrong Import in app.py**: **CRITICAL** - app.py must import from the modular mcp.mcp, not from a monolithic mcp_tools.py file. This was a major bug where the HTTP transport was serving tools from the wrong file, causing "cached" tool list behavior.

### Debugging Checklist

When MCP connections fail:

1. Check server logs: `docker compose logs backend`
2. Check client logs: `docker compose logs zeroclaw | grep -i "mcp\|tool"`
3. Verify URLs match: ZeroClaw config vs server mount path
4. Test connectivity: `curl http://localhost:8000/mcp`
5. Check container networking: `docker exec zeroclaw curl http://backend:8000/mcp`
6. Validate Python imports: Ensure `__init__.py` files exist

## Current Status

- ✅ Basic MCP server infrastructure working
- ✅ HTTP transport connection to ZeroClaw established
- ✅ 2 MCP tools (echo, sync_garmin_activities) — simplified from original 9
- ✅ Docker deployment functional
- ✅ Request/response logging middleware implemented
- ✅ Tool-level logging for debugging
- ✅ Garmin API client implemented with authentication
- ✅ Activity ingestion script with pagination
- ✅ PostgreSQL database schema with activities table
- ✅ Neon PostgreSQL database integration
- ✅ pgAdmin service for database management
- ✅ Changepoint detection service using ruptures library
- ✅ Activity interval detection MCP tool
- ✅ Workout metadata tools for RPE, feeling, and session structure
- ✅ Modular MCP architecture with separate tool modules (garmin, workout, analysis)
- ✅ Database initialization via Alembic migrations
- ✅ Tool execution testing in progress (requires user approval in ZeroClaw)
- ✅ Fixed app.py import to use modular mcp.mcp instead of monolithic mcp_tools.py
- ✅ Added get_hr_10sec_averages tool for interval detection testing
- ✅ Removed hardcoded secrets from config.toml, using environment variables
- ✅ Added PYTHONDONTWRITEBYTECODE=1 to prevent Python bytecode cache issues

**Next Priority**: Implement additional MCP tools for advanced analysis and LLM integration.

---

## Phase 2: API Client Integration

### 2.1 Garmin Client

- [x] Create `backend/app/clients/garmin.py` using python-garminconnect library
- [x] Implement authentication with email/password
- [x] Implement `get_activities()` method with pagination
- [x] Implement `get_activity_details()` method
- [x] Implement `get_activity_samples()` method for heart rate data
- [x] Test authentication with Garmin Connect

### 2.2 Changepoint Detection Service

- [x] Create `backend/app/services/changepoint_detection.py` using ruptures library
- [x] Implement PELT algorithm for interval detection
- [x] Add configurable penalty parameter for sensitivity
- [x] Implement signal smoothing for noise reduction
- [x] Add multivariate detection support (HR + cadence + power)
- [x] Test on indoor cardio activity

---

## Phase 3: MCP Protocol Implementation

### 3.1 FastAPI + FastMCP Server

- [x] Create `backend/app/mcp/mcp.py` with FastMCP orchestrator
- [x] Implement modular tool structure with separate modules:
  - app/mcp/garmin/tools.py - Garmin-related tools
  - app/mcp/workout/tools.py - Workout metadata tools
  - app/mcp/analysis/tools.py - Analysis tools
- [x] Implement 8 MCP tools with @mcp.tool() decorators:
  - get_recent_activities
  - get_garmin_data
  - analyze_activity
  - echo
  - sync_garmin_activities
  - get_pending_metadata
  - save_workout_metadata
  - detect_activity_intervals
- [x] Mount FastMCP server at `/mcp` endpoint for HTTP transport (ZeroClaw)
- [x] Add FastAPI health check endpoint at `/health`
- [ ] Implement additional tools as needed:
  - get_activity_details
  - get_activity_by_date_range
  - get_activity_hr_data
  - compare_activities
  - get_training_load

### 3.2 Tool Helper Functions

- [x] Implement input validation for all tools
- [x] Add error handling for all tools
- [ ] Implement `aggregate_hr_buckets()` for HR data aggregation
- [ ] Implement `extract_metric()` for activity metric extraction

---

## Phase 4: Docker Setup & Deployment

### 4.1 Build and Start Services

- [x] Configure `.env` with actual credentials
- [x] Run `docker-compose up -d --build`
- [x] Verify all containers start successfully
- [x] Check `docker-compose ps` status

### 4.2 Database Setup

- [x] Database initialization runs automatically on startup
- [x] Verify tables created in PostgreSQL via pgAdmin
- [x] Test database connection

### 4.3 MCP Server Verification

- [x] Test FastAPI health check: `curl http://localhost:8000/health`
- [x] Test MCP endpoint: `curl http://localhost:8000/mcp`
- [x] Verify tools are registered via logs
- [x] Test tool execution via HTTP endpoint
- [x] Check logs: `docker-compose logs -f backend`

---

## Phase 5: Data Ingestion

### 5.1 Create Ingestion Scripts

- [x] Create `backend/scripts/ingest_activities.py` for initial data import
- [x] Test Garmin data ingestion with pagination
- [x] Verify activities in database
- [x] Create `sync_garmin_activities` MCP tool for periodic sync
- [x] Test HR data extraction from Garmin API

### 5.2 Populate Database

- [x] Run initial Garmin ingestion (100 recent activities)
- [x] Verify activities in database
- [x] Test activity interval detection on sample data
- [x] Verify HR data for activities
- [x] Test queries against populated database

---

## Phase 6: Testing with MCP Tools

### 6.1 Test Activity Tools

- [x] Test `get_recent_activities` with filters
- [x] Test `sync_garmin_activities` with Garmin Connect
- [ ] Test `get_activity_details` with HR data
- [ ] Test `get_activity_by_date_range`
- [x] Test `detect_activity_intervals` with different penalty values

### 6.2 Test HR Data Tools

- [ ] Test `get_activity_hr_data` with bucketing
- [ ] Verify HR aggregation works correctly

### 6.3 Test Analysis Tools

- [ ] Test `compare_activities` with multiple activities
- [ ] Test `get_training_load` for various time periods

### 6.4 Test User Data Tools

- [x] Test `get_pending_metadata`
- [x] Test `save_workout_metadata`
- [ ] Test `get_user_feedback` (when implemented)
- [ ] Test `get_llm_summary` (when implemented)

---

## Phase 7: ZeroClaw Integration

### 7.1 ZeroClaw Setup

- [x] ZeroClaw Docker configuration created
- [x] Configure ZeroClaw MCP connection (HTTP transport to backend:8000/mcp)
- [x] Set up LLM provider configuration in config.toml
- [ ] Configure ZeroClaw channels (Discord, Telegram, CLI, etc.)
- [x] Test tool calls through ZeroClaw
- [x] Test conversational queries
- [x] Test multi-step tool chaining

---

## Phase 8: Testing & Verification

### 8.1 ZeroClaw Testing

- [ ] Test all 8 Garmin MCP tools through ZeroClaw
- [ ] Test channel integrations (Discord, Telegram, CLI)
- [ ] Test SOP engine with Garmin tools
- [ ] Test approval gates for high-risk operations
- [ ] Test tool receipts and audit logging
- [ ] Verify privacy guarantees (local execution if using Ollama)

### 8.2 Performance Testing

- [ ] Test with large activity datasets
- [ ] Test concurrent tool calls
- [ ] Test memory usage under load
- [ ] Test response times

---

## Dependencies & Prerequisites

### Required Software

- Docker Desktop
- Python 3.12+
- ZeroClaw

### Required Accounts

- Garmin Connect account
- LLM provider account (Anthropic, OpenAI, or Ollama for local)

### Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `GARMIN_EMAIL` - Garmin login email
- `GARMIN_PASSWORD` - Garmin login password
- `ANTHROPIC_API_KEY` - Anthropic API key for ZeroClaw
- `OPENAI_API_KEY` - OpenAI API key for ZeroClaw

---

## Success Criteria Checklist

### Infrastructure

- [x] Docker container starts successfully
- [x] PostgreSQL database initialized with correct schema (Neon)
- [x] FastAPI server accessible at http://localhost:8000
- [x] MCP endpoint accessible at http://localhost:8000/mcp
- [x] pgAdmin accessible at http://localhost:5050

### MCP Server

- [x] FastMCP server starts successfully
- [x] FastMCP mounts at /mcp endpoint
- [x] 5 tools are registered and discoverable
- [x] Tool execution works correctly via HTTP endpoint
- [x] Garmin data retrieval works
- [x] PostgreSQL queries work
- [x] Error handling works properly
- [x] HR data extraction from Garmin API works
- [x] Changepoint detection works with ruptures library
- [ ] HR data aggregation works

### Data Ingestion

- [x] Garmin activities successfully ingested (100 activities)
- [x] Activity intervals detected and stored
- [ ] HR time series data stored correctly
- [x] Database queries return expected results

### ZeroClaw Integration

- [ ] FastMCP server connects via HTTP at /mcp endpoint
- [ ] ZeroClaw can call tools successfully
- [ ] Channel integrations work (Discord, Telegram, CLI)
- [ ] Conversational queries work
- [ ] Multi-step chaining works
- [ ] SOP engine works with Garmin tools
- [ ] Approval gates function correctly

---

## Notes

- ZeroClaw uses HTTP transport to connect to MCP server at localhost:8000/mcp
- Hot reload is enabled in docker-compose for development
- Use pgAdmin at http://localhost:5050 for database inspection and queries
- All environment variables must be set in `.env` file
- Never commit `.env` file to version control
- ZeroClaw supports 30+ channels - configure as needed
- **zeroclaw-web/** directory contains the full ZeroClaw repository for reference/customization
- Changepoint detection uses ruptures library with PELT algorithm
- Garmin API requires authentication and has rate limits (429 errors)
- Heart rate data extracted from Garmin activityDetailMetrics at index 2 (directHeartRate)
- Activity intervals stored in activity_intervals table with HR statistics

## Related Files

- `backend/app/mcp/mcp.py` - FastMCP server orchestrator
- `backend/app/mcp/garmin/tools.py` - Garmin-related tools
- `backend/app/mcp/workout/tools.py` - Workout metadata tools
- `backend/app/mcp/analysis/tools.py` - Analysis tools
- `backend/app/core/database.py` - Database configuration
- `backend/app/core/config.py` - Application configuration
- `zeroclaw/config.toml` - ZeroClaw MCP client configuration
- `docker-compose.yml` - Container orchestration
- `backend/requirements.txt` - Python dependencies
