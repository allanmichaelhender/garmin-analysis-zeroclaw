"""Analysis MCP tools (deprecated — import works but not registered in mcp.py)."""

import logging
from app.core.database import SessionLocal
from app.models.models import Activity

logger = logging.getLogger("mcp.analysis")


def register_tools(mcp):
    """Register analysis tools with the FastMCP instance."""

    @mcp.tool()
    def detect_activity_intervals(
        activity_id: str, penalty: float = 50.0, model: str = "rbf"
    ) -> str:
        """Deprecated — analysis tools have been removed."""
        return "Analysis tools are deprecated. Activity data is stored in the activities table via sync_garmin_activities."
