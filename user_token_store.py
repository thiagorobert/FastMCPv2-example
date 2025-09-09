import json
import asyncio
import time
from typing import Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserTokens:
    """User token storage data structure."""
    user_id: str
    github_access_token: Optional[str] = None
    github_refresh_token: Optional[str] = None
    github_expires_at: Optional[float] = None
    oauth_access_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    oauth_expires_at: Optional[float] = None
    created_at: float = None
    updated_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        self.updated_at = time.time()
    
    def is_github_token_expired(self) -> bool:
        """Check if GitHub token is expired."""
        if not self.github_expires_at:
            return False
        return time.time() >= self.github_expires_at
    
    def is_oauth_token_expired(self) -> bool:
        """Check if OAuth token is expired."""
        if not self.oauth_expires_at:
            return False
        return time.time() >= self.oauth_expires_at


class UserTokenStore:
    """
    Token storage system for managing user GitHub tokens.
    
    In a production system, this would be replaced with a proper database
    like PostgreSQL, Redis, or MongoDB. For this demo, we use file-based storage.
    """
    
    def __init__(self, storage_path: str = ".user_tokens"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self._lock = asyncio.Lock()
        logger.info(f"Initialized UserTokenStore with storage path: {self.storage_path}")
    
    def _get_user_file_path(self, user_id: str) -> Path:
        """Get the file path for a specific user's tokens."""
        # Sanitize user_id for filename
        safe_user_id = "".join(c for c in user_id if c.isalnum() or c in ('-', '_', '.'))
        return self.storage_path / f"{safe_user_id}.json"
    
    async def store_user_tokens(self, user_tokens: UserTokens) -> None:
        """Store user tokens to persistent storage."""
        async with self._lock:
            file_path = self._get_user_file_path(user_tokens.user_id)
            
            try:
                user_tokens.updated_at = time.time()
                with open(file_path, 'w') as f:
                    json.dump(asdict(user_tokens), f, indent=2)
                
                logger.info(f"Stored tokens for user: {user_tokens.user_id}")
                
            except Exception as e:
                logger.error(f"Failed to store tokens for user {user_tokens.user_id}: {e}")
                raise
    
    async def get_user_tokens(self, user_id: str) -> Optional[UserTokens]:
        """Retrieve user tokens from persistent storage."""
        async with self._lock:
            file_path = self._get_user_file_path(user_id)
            
            if not file_path.exists():
                logger.debug(f"No tokens found for user: {user_id}")
                return None
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                user_tokens = UserTokens(**data)
                logger.debug(f"Retrieved tokens for user: {user_id}")
                return user_tokens
                
            except Exception as e:
                logger.error(f"Failed to retrieve tokens for user {user_id}: {e}")
                return None
    
    async def get_github_token(self, user_id: str) -> Optional[str]:
        """Get a valid GitHub access token for a user."""
        user_tokens = await self.get_user_tokens(user_id)
        
        if not user_tokens or not user_tokens.github_access_token:
            logger.debug(f"No GitHub token found for user: {user_id}")
            return None
        
        if user_tokens.is_github_token_expired():
            logger.info(f"GitHub token expired for user: {user_id}")
            # In a real implementation, we would attempt token refresh here
            return None
        
        return user_tokens.github_access_token
    
    async def update_github_token(
        self, 
        user_id: str, 
        access_token: str, 
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None
    ) -> None:
        """Update GitHub token for a user."""
        user_tokens = await self.get_user_tokens(user_id)
        
        if not user_tokens:
            user_tokens = UserTokens(user_id=user_id)
        
        user_tokens.github_access_token = access_token
        user_tokens.github_refresh_token = refresh_token
        
        if expires_in:
            user_tokens.github_expires_at = time.time() + expires_in
        
        await self.store_user_tokens(user_tokens)
        logger.info(f"Updated GitHub token for user: {user_id}")
    
    async def update_oauth_token(
        self, 
        user_id: str, 
        access_token: str, 
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None
    ) -> None:
        """Update OAuth token for a user."""
        user_tokens = await self.get_user_tokens(user_id)
        
        if not user_tokens:
            user_tokens = UserTokens(user_id=user_id)
        
        user_tokens.oauth_access_token = access_token
        user_tokens.oauth_refresh_token = refresh_token
        
        if expires_in:
            user_tokens.oauth_expires_at = time.time() + expires_in
        
        await self.store_user_tokens(user_tokens)
        logger.info(f"Updated OAuth token for user: {user_id}")
    
    async def delete_user_tokens(self, user_id: str) -> bool:
        """Delete all tokens for a user."""
        async with self._lock:
            file_path = self._get_user_file_path(user_id)
            
            if not file_path.exists():
                return False
            
            try:
                file_path.unlink()
                logger.info(f"Deleted tokens for user: {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete tokens for user {user_id}: {e}")
                return False
    
    async def list_users(self) -> list[str]:
        """List all users with stored tokens."""
        try:
            user_files = list(self.storage_path.glob("*.json"))
            users = [f.stem for f in user_files]
            return users
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens. Returns number of users cleaned up."""
        users = await self.list_users()
        cleaned_count = 0
        
        for user_id in users:
            user_tokens = await self.get_user_tokens(user_id)
            if not user_tokens:
                continue
            
            # Check if both tokens are expired
            github_expired = user_tokens.is_github_token_expired()
            oauth_expired = user_tokens.is_oauth_token_expired()
            
            if github_expired and oauth_expired:
                await self.delete_user_tokens(user_id)
                cleaned_count += 1
                logger.info(f"Cleaned up expired tokens for user: {user_id}")
        
        return cleaned_count


# Global token store instance
token_store = UserTokenStore()