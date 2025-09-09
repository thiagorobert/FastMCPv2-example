import os
from fastmcp import FastMCP
import logging
from starlette.responses import JSONResponse
from auth_provider import AuthProvider, AuthProviderFactory
import github_api
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Optional GitHub access token (now used as fallback only)
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
if GITHUB_ACCESS_TOKEN:
    logging.info("GITHUB_ACCESS_TOKEN found - will be used as fallback for unauthenticated requests")
else:
    logging.info("GITHUB_ACCESS_TOKEN not set - using dynamic token management only")

# Auth provider selection from environment variable
AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "auth0").lower()

# Create auth provider based on selection
try:
    auth_provider_type = AuthProvider(AUTH_PROVIDER)
except ValueError:
    logging.warning(f"Unknown auth provider '{AUTH_PROVIDER}', defaulting to auth0")
    auth_provider_type = AuthProvider.AUTH0

logging.info(f"Using auth provider: {auth_provider_type.value}")
auth_provider = AuthProviderFactory.create_provider(auth_provider_type)

# FastMCP server with authentication
mcp = FastMCP("github_oauth_example", auth=auth_provider)


# OAuth Authorization Server Metadata endpoint
@mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
async def oauth_authorization_server(_request):
    """OAuth 2.0 Authorization Server Metadata endpoint (RFC 8414)"""
    from starlette.responses import RedirectResponse
    metadata_url = AuthProviderFactory.get_oauth_metadata_url(auth_provider_type)
    return RedirectResponse(url=metadata_url)


# Health check
@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request):
    return JSONResponse({"status": "healthy", "service": "github_oauth_example"})


@mcp.tool()
async def list_repositories() -> str:
    """List all repositories accessible to the authenticated user."""
    # Try to get user ID from the current request context
    user_id = None
    try:
        # In FastMCP with JWT auth, the client_id is typically available in the token
        # For this implementation, we'll use the JWT subject (sub) claim as user_id
        from fastmcp.server.context import get_request_context
        context = get_request_context()
        if hasattr(context, 'user') and context.user:
            user_id = getattr(context.user, 'sub', None)
            if not user_id:
                user_id = getattr(context.user, 'client_id', None)
            
            # Debug: Log what we found in the JWT for troubleshooting
            logger.info(f"JWT context debug - sub: {getattr(context.user, 'sub', None)}, client_id: {getattr(context.user, 'client_id', None)}")
            if hasattr(context.user, '__dict__'):
                logger.info(f"Available JWT claims: {list(context.user.__dict__.keys())}")
    except Exception as e:
        # If context is not available or user is not authenticated, user_id remains None
        logger.debug(f"Failed to get user context: {e}")
        pass
    
    return await github_api.list_repositories(user_id)

@mcp.tool()
async def get_repository_info(owner: str, repo: str) -> str:
    """Get detailed information about a specific repository.

    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
    """
    # Try to get user ID from the current request context
    user_id = None
    try:
        from fastmcp.server.context import get_request_context
        context = get_request_context()
        if hasattr(context, 'user') and context.user:
            user_id = getattr(context.user, 'sub', None)
            if not user_id:
                user_id = getattr(context.user, 'client_id', None)
            
            # Debug: Log what we found in the JWT for troubleshooting
            logger.info(f"JWT context debug - sub: {getattr(context.user, 'sub', None)}, client_id: {getattr(context.user, 'client_id', None)}")
            if hasattr(context.user, '__dict__'):
                logger.info(f"Available JWT claims: {list(context.user.__dict__.keys())}")
    except Exception as e:
        logger.debug(f"Failed to get user context: {e}")
        pass
    
    return await github_api.get_repository_info(owner, repo, user_id)

@mcp.tool()
async def get_user_info() -> str:
    """Get information about the authenticated user."""
    # Try to get user ID from the current request context
    user_id = None
    try:
        from fastmcp.server.context import get_request_context
        context = get_request_context()
        if hasattr(context, 'user') and context.user:
            user_id = getattr(context.user, 'sub', None)
            if not user_id:
                user_id = getattr(context.user, 'client_id', None)
            
            # Debug: Log what we found in the JWT for troubleshooting
            logger.info(f"JWT context debug - sub: {getattr(context.user, 'sub', None)}, client_id: {getattr(context.user, 'client_id', None)}")
            if hasattr(context.user, '__dict__'):
                logger.info(f"Available JWT claims: {list(context.user.__dict__.keys())}")
    except Exception as e:
        logger.debug(f"Failed to get user context: {e}")
        pass
    
    return await github_api.get_user_info(user_id)

# Create ASGI application (used by run_asgi.sh)
app = mcp.http_app(transport='streamable-http')


if __name__ == "__main__":
    # Run the MCP via stdio (used by test_mcp_using_claude.sh)
    mcp.run(transport='stdio')

