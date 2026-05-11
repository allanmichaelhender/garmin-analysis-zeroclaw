"""FastAPI server setup for Garmin MCP server."""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import Response
from app.mcp_tools import http_app, sse_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app")

# Create FastAPI app with shared lifespan from MCP
app = FastAPI(lifespan=http_app.lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks."""
    return {"status": "healthy"}


# Add middleware to log all requests and responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and outgoing responses."""
    # Log request
    logger.info(f"🔵 REQUEST: {request.method} {request.url.path}")
    
    # Log request body if present (for POST requests)
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                logger.info(f"🔵 REQUEST BODY: {body.decode()}")
        except Exception as e:
            logger.error(f"Error reading request body: {e}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    logger.info(f"🟢 RESPONSE: {response.status_code}")
    
    # Try to log response body for JSON responses
    if response.headers.get("content-type", "").startswith("application/json"):
        try:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            if body:
                logger.info(f"🟢 RESPONSE BODY: {body.decode()}")
            # Recreate response with the body
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        except Exception as e:
            logger.error(f"Error reading response body: {e}")
    
    return response


# Mount the FastMCP HTTP app at /mcp and SSE endpoint at /mcp/sse
app.mount("/mcp", http_app)
app.mount("/mcp/sse", sse_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
