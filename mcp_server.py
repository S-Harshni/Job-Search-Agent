import os
import logging
import asyncio
from contextlib import asynccontextmanager
from agents.mcp import MCPServerStdio

logger = logging.getLogger(__name__)


@asynccontextmanager
async def open_mcp_server(api_token: str | None = None, browser_auth: str | None = None):
    """Start the Bright Data MCP server (via npx) for one analysis run and close it afterwards.

    Credentials come from the caller (the Streamlit sidebar) and fall back to the
    BRIGHT_DATA_API_KEY / BROWSER_AUTH environment variables. BROWSER_AUTH is optional:
    it only enables Bright Data's scraping-browser tools.
    """
    token = api_token or os.environ.get("BRIGHT_DATA_API_KEY")
    if not token:
        raise ValueError("A Bright Data API token is required.")
    env = {"API_TOKEN": token, "WEB_UNLOCKER_ZONE": "mcp_unlocker", "PATH": os.environ.get("PATH", "")}
    auth = browser_auth or os.environ.get("BROWSER_AUTH")
    if auth:
        env["BROWSER_AUTH"] = auth

    server = MCPServerStdio(cache_tools_list=False, params={"command": "npx", "args": ["-y", "@brightdata/mcp"], "env": env})
    await asyncio.wait_for(server.__aenter__(), timeout=60)
    try:
        yield server
    finally:
        try:
            await server.__aexit__(None, None, None)
        except Exception as exc:  # shutting down should never hide the real result
            logger.warning("Error closing MCP server: %s", exc)
