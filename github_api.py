import httpx
import os
import logging
from typing import Any, Optional
from dotenv import load_dotenv
from user_token_store import token_store

# Load environment variables from .env file
load_dotenv()

# Import Auth0 GitHub integration for fallback
try:
    from auth0_github_integration import get_github_token_from_auth0
    AUTH0_INTEGRATION_AVAILABLE = True
except ImportError:
    AUTH0_INTEGRATION_AVAILABLE = False
    get_github_token_from_auth0 = None

GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "github-oauth-mcp/1.0"

logger = logging.getLogger(__name__)


def load_token() -> Optional[str]:
    """Load GitHub access token from environment variable (fallback only)."""
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        logger.warning("GITHUB_ACCESS_TOKEN environment variable not set - no fallback token available")
        return None

    logger.info("Token loaded from GITHUB_ACCESS_TOKEN environment variable")
    return token


async def get_user_github_token(user_id: str) -> Optional[str]:
    """Get GitHub token for a specific user from the token store or Auth0."""
    try:
        # First try the local token store (for local OAuth flow)
        token = await token_store.get_github_token(user_id)
        if token:
            logger.info(f"Retrieved GitHub token from local store for user: {user_id}")
            return token
        
        # If no local token and Auth0 integration is available, try Auth0
        if AUTH0_INTEGRATION_AVAILABLE and get_github_token_from_auth0:
            logger.info(f"Trying Auth0 GitHub integration for user: {user_id}")
            auth0_token = await get_github_token_from_auth0(user_id)
            if auth0_token:
                logger.info(f"Retrieved GitHub token from Auth0 for user: {user_id}")
                # Store it locally for future use
                await token_store.update_github_token(
                    user_id=user_id,
                    access_token=auth0_token,
                    expires_in=3600  # 1 hour default
                )
                return auth0_token
        
        logger.warning(f"No GitHub token found for user: {user_id}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to retrieve GitHub token for user {user_id}: {e}")
        return None


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
            logger.error(f"GitHub API request failed: {e}")
            return None


async def list_repositories(user_id: Optional[str] = None) -> str:
    """List all repositories accessible to the authenticated user."""
    
    # Try to get user's GitHub token first, fallback to environment token
    token = None
    if user_id:
        token = await get_user_github_token(user_id)
    
    if not token:
        logger.info("Using fallback GITHUB_ACCESS_TOKEN from environment")
        token = load_token()
        if not token:
            return "Unable to fetch repositories. Please authenticate with GitHub through OAuth or set GITHUB_ACCESS_TOKEN environment variable."

    url = f"{GITHUB_API_BASE}/user/repos"
    data = await make_github_request(url, token)

    if not data:
        return "Unable to fetch repositories. Please ensure you have GitHub access configured."

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


async def get_repository_info(owner: str, repo: str, user_id: Optional[str] = None) -> str:
    """Get detailed information about a specific repository.

    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        user_id: User ID for token lookup
    """
    
    # Try to get user's GitHub token first, fallback to environment token
    token = None
    if user_id:
        token = await get_user_github_token(user_id)
    
    if not token:
        logger.info("Using fallback GITHUB_ACCESS_TOKEN from environment")
        token = load_token()
        if not token:
            return f"Unable to fetch information for repository {owner}/{repo}. Please authenticate with GitHub through OAuth or set GITHUB_ACCESS_TOKEN environment variable."

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    data = await make_github_request(url, token)

    if not data:
        return f"Unable to fetch information for repository {owner}/{repo}. Please ensure you have GitHub access configured."

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


async def get_user_info(user_id: Optional[str] = None) -> str:
    """Get information about the authenticated user."""
    
    # Try to get user's GitHub token first, fallback to environment token
    token = None
    if user_id:
        token = await get_user_github_token(user_id)
    
    if not token:
        logger.info("Using fallback GITHUB_ACCESS_TOKEN from environment")
        token = load_token()
        if not token:
            return "Unable to fetch user information. Please authenticate with GitHub through OAuth or set GITHUB_ACCESS_TOKEN environment variable."
    
    url = f"{GITHUB_API_BASE}/user"
    data = await make_github_request(url, token)

    if not data:
        return "Unable to fetch user information. Please ensure you have GitHub access configured."

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
