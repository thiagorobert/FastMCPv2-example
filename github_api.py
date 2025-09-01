import httpx
import os
import logging
from typing import Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "github-oauth-mcp/1.0"

logger = logging.getLogger(__name__)


def load_token() -> str:
    """Load GitHub access token from environment variable."""
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_ACCESS_TOKEN environment variable is required")

    logger.info("Token loaded from GITHUB_ACCESS_TOKEN environment variable")
    return token


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
