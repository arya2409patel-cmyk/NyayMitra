"""Fetch the tools from the running MCP server at runtime (not imported)."""
import asyncio
import config

async def fetch_tools_async():
    from langchain_mcp_adapters.client import MultiServerMCPClient
    client = MultiServerMCPClient({"nyaymitra": {"url": config.MCP_URL, "transport": "streamable_http"}})
    return await client.get_tools()

def fetch_mcp_tools():
    return asyncio.run(fetch_tools_async())
