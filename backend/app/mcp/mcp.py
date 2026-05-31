"""FastMCP core orchestrator - creates MCP instance and registers all tools."""

import logging
from fastmcp import FastMCP
from dotenv import load_dotenv
from app.mcp.garmin import tools as garmin_tools
from app.mcp.garmin import summary as garmin_summary

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

# Register Garmin tool modules
garmin_tools.register_tools(mcp)
garmin_summary.register_tools(mcp)

logger.info(
    "Registered MCP tools: echo, sync_garmin_activities, update_workout_metadata, "
    "analyze_hr_profile, get_activity_summary"
)
