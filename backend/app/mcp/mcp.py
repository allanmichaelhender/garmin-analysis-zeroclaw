"""FastMCP core orchestrator - creates MCP instance and registers all tools."""

import logging
from fastmcp import FastMCP
from dotenv import load_dotenv
from app.mcp.garmin import tools as garmin_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp")

# Load environment variables
load_dotenv()

# Create FastMCP instance
mcp = FastMCP("garmin-mcp-server")
http_app = mcp.http_app(path="/", transport="http")
sse_app = mcp.http_app(path="/", transport="sse")

# Register Garmin tool module
garmin_tools.register_tools(mcp)

logger.info("Registered MCP tools: echo, sync_garmin_activities")
