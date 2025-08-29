
import asyncio
from datetime import datetime
from fastmcp import Client
from fastmcp.client.auth import OAuth
import pathlib

STAMP = datetime.now().strftime("%Y%m%d%H%M%S")

oauth = OAuth(client_name=f"client_{STAMP}",
              mcp_url="http://127.0.0.1:8080/mcp",
              callback_port=8081,
              token_storage_cache_dir=pathlib.Path(".fastmcp/oauth-mcp-client-cache"))

async def main():
    async with Client("http://127.0.0.1:8080/mcp", auth=oauth) as client:
        await client.ping()


if __name__ == "__main__":
    asyncio.run(main())