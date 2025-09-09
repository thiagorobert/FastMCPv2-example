
import asyncio
from datetime import datetime
from fastmcp import Client
from fastmcp.client.auth import OAuth
import pathlib
from dotenv import load_dotenv

# Load environment variables from .env file
# Only relevant for Keycloak, since env variable KEYCLOAK_INITIAL_ACCESS_TOKEN
# is required in that flow
load_dotenv()


STAMP = datetime.now().strftime("%Y%m%d%H%M%S")
SERVER_URL = "http://127.0.0.1:8080"
CALBACK_PORT = 8082
OAUTH = OAuth(client_name=f"client_{STAMP}",
              mcp_url=f"{SERVER_URL}/mcp",
              callback_port=CALBACK_PORT,
              # Make the cache directory unique when testing dynamic client creation
              # to avoid re-using credentials for preexisting clients
              token_storage_cache_dir=pathlib.Path(f".fastmcp/oauth-mcp-client-cache/{STAMP}"),
              # This is only relevant for the Auth0 flow. Without audience set, Auth0 issues
              # opaue access_tokens (not jwt)
              additional_client_metadata={"audience": "aud"},
              )

async def main():
    async with Client(f"{SERVER_URL}/mcp", auth=OAUTH) as client:
        await client.ping()

        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")

        if tools:
            first_tool = tools[0]
            print(f"\nCalling tool: {first_tool.name}")
            result = await client.call_tool(first_tool.name, {})
            print(f"Result: {result.__class__}")
            print(result)


if __name__ == "__main__":
    asyncio.run(main())
