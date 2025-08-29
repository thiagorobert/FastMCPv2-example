import httpx
import json
from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from pydantic import AnyHttpUrl
from typing import Any
from starlette.responses import JSONResponse

GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "github-oauth-mcp/1.0"
TOKEN_FILE = "github_token.json"  # Token storage file

# Configure Auth0 authentication
auth0_domain = "https://rfc7591-test.us.auth0.com"

# Configure token validation for Auth0
token_verifier = JWTVerifier(
    jwks_uri=f"{auth0_domain}/.well-known/jwks.json",
    issuer=auth0_domain,
    audience="mcp-production-api"
)

# Create the remote auth provider
auth = RemoteAuthProvider(
    token_verifier=token_verifier,
    authorization_servers=[AnyHttpUrl(auth0_domain)],
    resource_server_url="https://api.yourcompany.com"
)

# FastMCP server with authentication
mcp = FastMCP("github_oauth_example", auth=auth)

# Health check
@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request):
    return JSONResponse({"status": "healthy", "service": "github_oauth_example"})

# OAuth Authorization Server Metadata endpoint
@mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
async def oauth_authorization_server(_request):
    """OAuth 2.0 Authorization Server Metadata endpoint (RFC 8414)"""
    metadata = {
        "issuer": auth0_domain,
        "authorization_endpoint": f"{auth0_domain}/authorize",
        "token_endpoint": f"{auth0_domain}/oauth/token",
        "jwks_uri": f"{auth0_domain}/.well-known/jwks.json",
        "userinfo_endpoint": f"{auth0_domain}/userinfo",
        "response_types_supported": ["code", "token", "id_token", "code token", "code id_token", "token id_token", "code token id_token"],
        "grant_types_supported": ["authorization_code", "implicit", "refresh_token", "client_credentials"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "claims_supported": ["sub", "iss", "aud", "exp", "iat", "auth_time", "nonce", "name", "email", "email_verified"],

        "registration_endpoint": f"{auth0_domain}/oidc/register"
    }
    return JSONResponse(metadata)


def load_token() -> str:
    """Load access github access token from file."""
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
    
    # Check if token exists
    if "access_token" not in token_data:
        raise RuntimeError(f"Github access token expected in {TOKEN_FILE}")

    # TODO: check if token is expired

    print(f"Token loaded from {TOKEN_FILE}")
    return token_data["access_token"]


async def make_github_request(url: str, token: str = None) -> dict[str, Any] | None:
    """Make a request to the GitHub API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GitHub API request failed: {e}")
            return None

@mcp.tool()
async def list_repositories() -> str:
    """List all repositories accessible to the authenticated user."""
    
    url = f"{GITHUB_API_BASE}/user/repos"
    data = await make_github_request(url, load_token())
    
    if not data:
        return "Unable to fetch repositories."
    
    repos = []
    for repo in data:
        repo_info = f"""
Repository: {repo['full_name']}
Description: {repo.get('description', 'No description')}
Language: {repo.get('language', 'Unknown')}
Stars: {repo['stargazers_count']}
Private: {repo['private']}
URL: {repo['html_url']}
"""
        repos.append(repo_info)
    
    return "\n---\n".join(repos)

@mcp.tool()
async def get_repository_info(owner: str, repo: str) -> str:
    """Get detailed information about a specific repository.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
    """
    
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    data = await make_github_request(url, load_token())
    
    if not data:
        return f"Unable to fetch information for repository {owner}/{repo}."
    
    return f"""
Repository: {data['full_name']}
Description: {data.get('description', 'No description')}
Language: {data.get('language', 'Unknown')}
Stars: {data['stargazers_count']}
Forks: {data['forks_count']}
Issues: {data['open_issues_count']}
Created: {data['created_at']}
Updated: {data['updated_at']}
Private: {data['private']}
URL: {data['html_url']}
Clone URL: {data['clone_url']}
"""

@mcp.tool()
async def get_user_info() -> str:
    """Get information about the authenticated user."""    
    url = f"{GITHUB_API_BASE}/user"
    data = await make_github_request(url, load_token())
    
    if not data:
        return "Unable to fetch user information."
    
    return f"""
Username: {data['login']}
Name: {data.get('name', 'Not set')}
Email: {data.get('email', 'Not public')}
Bio: {data.get('bio', 'No bio')}
Location: {data.get('location', 'Not set')}
Public Repos: {data['public_repos']}
Followers: {data['followers']}
Following: {data['following']}
Profile URL: {data['html_url']}
"""

# Create ASGI application
# transport: Literal["http", "streamable-http", "sse"]
app = mcp.http_app(transport='streamable-http')

if __name__ == "__main__":
    mcp.run(transport='stdio')

