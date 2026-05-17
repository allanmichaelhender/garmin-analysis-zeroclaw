# MCP Connection Setup Guide

## Overview

This guide documents the **correct way to set up MCP (Model Context Protocol) connections** between FastMCP servers and ZeroClaw clients. It includes common pitfalls and their solutions based on real troubleshooting experience.

## FastMCP Server Setup

### 1. Single FastMCP Instance Per Server

**❌ WRONG**: Multiple FastMCP instances in the same application

```python
# DON'T DO THIS - causes conflicts
mcp1 = FastMCP("server1")
mcp2 = FastMCP("server2")  # Conflict!
```

**✅ CORRECT**: One FastMCP instance per server

```python
# In backend/app/mcp/mcp.py
from fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp")

# Single MCP instance
mcp = FastMCP("garmin-mcp-server")
http_app = mcp.http_app(path="/", transport="http")
sse_app = mcp.http_app(path="/", transport="sse")

# Register tool modules
from app.mcp.garmin import tools as garmin_tools
from app.mcp.workout import tools as workout_tools
from app.mcp.analysis import tools as analysis_tools

garmin_tools.register_tools(mcp)
workout_tools.register_tools(mcp)
analysis_tools.register_tools(mcp)
```

### 2. Python Package Structure

**❌ WRONG**: Missing `__init__.py` files

```
backend/
├── app/
│   ├── mcp/
│   │   └── mcp.py  # Can't import this!
```

**✅ CORRECT**: Proper Python package structure

```
backend/
├── __init__.py         # Required!
├── app/
│   ├── __init__.py     # Required!
│   ├── mcp/
│   │   ├── __init__.py # Required!
│   │   └── mcp.py
```

### 3. FastMCP API Usage

**❌ WRONG**: Deprecated parameters

```python
mcp = FastMCP("server", prefix="garmin")  # prefix deprecated in v3.x
```

**✅ CORRECT**: Modern FastMCP v3.x API

```python
mcp = FastMCP("garmin-mcp-server")  # No prefix parameter
```

## ZeroClaw Client Configuration

### 1. Correct MCP URL Configuration

**❌ WRONG**: Incorrect transport endpoint

```toml
[mcp]
servers = [{name = "garmin", transport = "http", url = "http://backend:8000/mcp/sse"}]
```

**✅ CORRECT**: Match server mount path

```toml
[mcp]
servers = [{name = "garmin", transport = "http", url = "http://backend:8000/mcp"}]
```

### 2. Transport Type Selection

- **HTTP Transport**: `transport = "http"` - For REST-like communication
- **SSE Transport**: `transport = "sse"` - For real-time streaming (if implemented)

## Docker Configuration

### 1. Service Dependencies

**❌ WRONG**: Services start simultaneously without dependencies

```yaml
services:
  backend:
    # No depends_on
  zeroclaw:
    # No depends_on
```

**✅ CORRECT**: Proper service dependencies

```yaml
services:
  backend:
    # Backend starts first
  zeroclaw:
    depends_on:
      - backend # ZeroClaw waits for backend
```

### 2. Network Configuration

**❌ WRONG**: Using localhost in container configs

```yaml
# In zeroclaw config.toml
url = "http://localhost:8000/mcp" # Won't work from container
```

**✅ CORRECT**: Use service names for container networking

```yaml
# In zeroclaw config.toml
url = "http://backend:8000/mcp" # backend is the service name
```

## Common Error Patterns & Solutions

### Error: "MCP server not connected"

**Symptoms**:

- ZeroClaw logs show "0 tool(s) registered"
- Tools not available in agent

**Causes & Fixes**:

1. **Wrong URL**: Check ZeroClaw config matches server mount path
2. **Service not ready**: Add `depends_on` in docker-compose.yml
3. **Network issues**: Use service names, not localhost
4. **Server crash**: Check backend logs for Python errors

### Error: "ImportError: No module named 'app'"

**Symptoms**:

- Docker container fails to start
- "ModuleNotFoundError" in logs

**Fix**: Add `__init__.py` files to make proper Python packages.

### Error: "Multiple MCP instances detected"

**Symptoms**:

- Tools not registering properly
- Inconsistent behavior

**Fix**: Consolidate to single FastMCP instance per server.

### Error: "Wrong MCP tools visible" or "Cached tool list"

**Symptoms**:

- HTTP transport shows different tools than expected
- Tool changes don't appear in HTTP transport
- "Cached" behavior persists across rebuilds

**Cause**: `app.py` importing from wrong MCP module (monolithic vs modular)

**Fix**: Ensure `app.py` imports from the correct module:
```python
# CORRECT - imports from modular structure
from app.mcp.mcp import http_app, sse_app

# WRONG - imports from old monolithic file
from app.mcp_tools import http_app, sse_app
```

This was a critical bug where the HTTP transport was serving tools from an old monolithic `mcp_tools.py` file instead of the modular `mcp.mcp` structure, causing tool lists to appear "cached" or out of sync with code changes.

### Error: "Tool execution denied"

**Symptoms**:

- Tools are registered but calls fail with permission errors
- MCP server shows "4 tool(s) available" but tools don't execute

**Cause**: ZeroClaw security requires explicit approval for MCP tool execution.

**Fixes**:

1. **Add to auto-approve list** (Recommended):

   ```toml
   [autonomy]
   auto_approve = [
     "garmin__echo",
     "garmin__get_recent_activities",
     "garmin__get_garmin_data",
     "garmin__analyze_activity"
   ]
   ```

2. **For testing only**: Set `level = "full"` in `[autonomy]` section
3. **For production**: Accept approval prompts in ZeroClaw UI

## Testing MCP Connections

### 1. Health Check Endpoint

Add a health endpoint to verify server is running:

```python
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

Test with: `curl http://localhost:8000/health`

### 2. MCP Tool Verification

Check backend logs for tool execution:

```bash
docker compose logs backend -f
```

Expected output when tools are called:

```
🔵 REQUEST: POST /mcp
🔵 REQUEST BODY: {"jsonrpc":"2.0","method":"tools/call",...}
🔧 TOOL CALL: echo(message='hello world')
🔧 TOOL RESULT: echo -> 'Echo: hello world'
🟢 RESPONSE: 200
```

### 3. ZeroClaw Tool Registration

Check ZeroClaw logs for tool registration:

```bash
docker compose logs zeroclaw | grep -i "mcp\|tool"
```

Expected output:

```
MCP server `garmin` connected — 4 tool(s) available
MCP: 4 tool(s) registered from 1 server(s)
```

### 3. Tool Execution Test

Test via ZeroClaw webhook:

```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "Test the echo tool with hello world"}'
```

## Debugging Checklist

When MCP connections fail:

1. **Check server logs**: `docker compose logs backend`
2. **Check client logs**: `docker compose logs zeroclaw`
3. **Verify URLs**: Ensure ZeroClaw config matches server endpoints
4. **Test connectivity**: `curl http://localhost:8000/mcp` from host
5. **Check container networking**: `docker exec zeroclaw curl http://backend:8000/mcp`
6. **Validate Python imports**: Check for missing `__init__.py` files
7. **Review FastMCP version**: Ensure compatible API usage

## Best Practices

1. **Single Responsibility**: One MCP server per service
2. **Proper Lifespan**: Always use `lifespan=http_app.lifespan`
3. **Clear Naming**: Use descriptive server names
4. **Version Pinning**: Pin FastMCP and related dependencies
5. **Health Checks**: Implement `/health` endpoints
6. **Logging**: Enable detailed logging for debugging with middleware
7. **Documentation**: Document all MCP endpoints and tools
8. **Tool Logging**: Log tool calls and results for debugging

## Version Compatibility

- **FastMCP**: v3.2.4+ (tested)
- **ZeroClaw**: Latest stable (with MCP HTTP transport support)
- **Python**: 3.9+ (async support required)

## Related Files

- `backend/app/mcp/mcp.py` - FastMCP server orchestrator
- `backend/app/mcp/garmin/tools.py` - Garmin-related tools
- `backend/app/mcp/workout/tools.py` - Workout metadata tools
- `backend/app/mcp/analysis/tools.py` - Analysis tools
- `zeroclaw/config.toml` - ZeroClaw MCP client configuration
- `docker-compose.yml` - Container orchestration
- `backend/requirements.txt` - Python dependencies</content>
  <parameter name="filePath">c:\Users\allan\Documents\GitHub\garmin-analysis\.windsurf\mcp-connection-setup.md
