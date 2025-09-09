"""
Auth0 GitHub Integration Module

This module handles extracting GitHub access tokens from Auth0 social connections.
In a real Auth0 setup with GitHub social connection, the GitHub token is not
automatically available in the JWT - it requires using Auth0's Management API.
"""

import asyncio
import httpx
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class Auth0GitHubIntegration:
    """
    Integration class for extracting GitHub tokens from Auth0.
    
    Note: This requires:
    1. Auth0 GitHub social connection configured
    2. Management API access token
    3. Proper scopes for accessing user identities
    """
    
    def __init__(self):
        self.auth0_domain = os.getenv("AUTH0_DOMAIN", "rfc7591-test.us.auth0.com")
        self.management_token = os.getenv("AUTH0_MANAGEMENT_TOKEN")
        self.base_url = f"https://{self.auth0_domain}"
    
    async def get_github_token_for_user(self, user_id: str) -> Optional[str]:
        """
        Get GitHub access token for a user from Auth0.
        
        This uses Auth0's Management API to fetch the user's social connection
        and extract the GitHub access token if available.
        """
        if not self.management_token:
            logger.warning("AUTH0_MANAGEMENT_TOKEN not set - cannot fetch GitHub tokens from Auth0")
            return None
        
        try:
            # Get user details from Auth0 Management API
            user_details = await self._get_user_details(user_id)
            if not user_details:
                return None
            
            # Extract GitHub token from identities
            github_token = await self._extract_github_token(user_details)
            return github_token
            
        except Exception as e:
            logger.error(f"Failed to get GitHub token for user {user_id}: {e}")
            return None
    
    async def _get_user_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user details from Auth0 Management API."""
        url = f"{self.base_url}/api/v2/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.management_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to fetch user details from Auth0: {e}")
                return None
    
    async def _extract_github_token(self, user_details: Dict[str, Any]) -> Optional[str]:
        """
        Extract GitHub access token from user identities.
        
        Note: This only works if Auth0 is configured to store GitHub tokens
        and the Management API has proper scopes.
        """
        identities = user_details.get("identities", [])
        
        for identity in identities:
            if identity.get("provider") == "github":
                # GitHub access token might be in the identity
                access_token = identity.get("access_token")
                if access_token:
                    logger.info("Found GitHub access token in Auth0 identity")
                    return access_token
                
                # Some Auth0 configurations store tokens differently
                connection = identity.get("connection")
                if connection and "github" in connection.lower():
                    # Try to get token via additional API call if needed
                    pass
        
        logger.warning("No GitHub access token found in Auth0 user identities")
        return None
    
    async def simulate_github_token_for_demo(self, user_id: str) -> Optional[str]:
        """
        Simulate GitHub token retrieval for demo purposes.
        
        In a real implementation, this would be replaced by actual Auth0 integration.
        For the demo, we'll generate a simulated token based on the user.
        """
        # This is a simulation - in production you'd use real Auth0 API
        simulated_tokens = {
            # Map Auth0 user IDs to simulated GitHub tokens
            # In practice, these would come from Auth0's Management API
        }
        
        # For demo purposes, create a simulated token
        if user_id:
            simulated_token = f"github_token_auth0_{user_id[-8:]}"
            logger.info(f"Simulated GitHub token for Auth0 user: {simulated_token[:20]}...")
            return simulated_token
        
        return None


# Global instance
auth0_github = Auth0GitHubIntegration()


async def get_github_token_from_auth0(user_id: str) -> Optional[str]:
    """
    Main function to get GitHub token from Auth0.
    
    This tries to get the real token first, then falls back to simulation.
    """
    # Try real Auth0 integration first
    real_token = await auth0_github.get_github_token_for_user(user_id)
    if real_token:
        return real_token
    
    # Fall back to simulation for demo
    return await auth0_github.simulate_github_token_for_demo(user_id)