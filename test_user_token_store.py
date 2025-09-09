import pytest
import tempfile
import shutil
import time

from user_token_store import UserTokenStore, UserTokens


class TestUserTokens:
    """Test UserTokens data structure."""
    
    def test_user_tokens_creation(self):
        """Test UserTokens creation with defaults."""
        user_tokens = UserTokens(user_id="test_user")
        
        assert user_tokens.user_id == "test_user"
        assert user_tokens.github_access_token is None
        assert user_tokens.github_refresh_token is None
        assert user_tokens.github_expires_at is None
        assert user_tokens.oauth_access_token is None
        assert user_tokens.oauth_refresh_token is None
        assert user_tokens.oauth_expires_at is None
        assert user_tokens.created_at is not None
        assert user_tokens.updated_at is not None
    
    def test_user_tokens_with_data(self):
        """Test UserTokens creation with data."""
        user_tokens = UserTokens(
            user_id="test_user",
            github_access_token="gh_token_123",
            github_refresh_token="gh_refresh_456",
            github_expires_at=time.time() + 3600,
            oauth_access_token="oauth_token_789",
            oauth_refresh_token="oauth_refresh_101",
            oauth_expires_at=time.time() + 1800
        )
        
        assert user_tokens.github_access_token == "gh_token_123"
        assert user_tokens.github_refresh_token == "gh_refresh_456"
        assert user_tokens.oauth_access_token == "oauth_token_789"
        assert user_tokens.oauth_refresh_token == "oauth_refresh_101"
    
    def test_token_expiration_checks(self):
        """Test token expiration methods."""
        current_time = time.time()
        
        # Non-expired tokens
        user_tokens = UserTokens(
            user_id="test_user",
            github_expires_at=current_time + 3600,
            oauth_expires_at=current_time + 1800
        )
        
        assert not user_tokens.is_github_token_expired()
        assert not user_tokens.is_oauth_token_expired()
        
        # Expired tokens
        user_tokens_expired = UserTokens(
            user_id="test_user",
            github_expires_at=current_time - 3600,
            oauth_expires_at=current_time - 1800
        )
        
        assert user_tokens_expired.is_github_token_expired()
        assert user_tokens_expired.is_oauth_token_expired()
    
    def test_token_expiration_no_expiry_time(self):
        """Test token expiration when no expiry time is set."""
        user_tokens = UserTokens(user_id="test_user")
        
        # Should return False when no expiry time is set
        assert not user_tokens.is_github_token_expired()
        assert not user_tokens.is_oauth_token_expired()


class TestUserTokenStore:
    """Test UserTokenStore functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def token_store(self, temp_storage):
        """Create UserTokenStore with temporary storage."""
        return UserTokenStore(storage_path=temp_storage)
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_user_tokens(self, token_store):
        """Test storing and retrieving user tokens."""
        user_tokens = UserTokens(
            user_id="test_user",
            github_access_token="gh_token_123",
            github_refresh_token="gh_refresh_456",
            oauth_access_token="oauth_token_789"
        )
        
        # Store tokens
        await token_store.store_user_tokens(user_tokens)
        
        # Retrieve tokens
        retrieved_tokens = await token_store.get_user_tokens("test_user")
        
        assert retrieved_tokens is not None
        assert retrieved_tokens.user_id == "test_user"
        assert retrieved_tokens.github_access_token == "gh_token_123"
        assert retrieved_tokens.github_refresh_token == "gh_refresh_456"
        assert retrieved_tokens.oauth_access_token == "oauth_token_789"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_user_tokens(self, token_store):
        """Test retrieving tokens for non-existent user."""
        result = await token_store.get_user_tokens("nonexistent_user")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_github_token(self, token_store):
        """Test getting GitHub token for user."""
        user_tokens = UserTokens(
            user_id="test_user",
            github_access_token="gh_token_123",
            github_expires_at=time.time() + 3600
        )
        
        await token_store.store_user_tokens(user_tokens)
        
        # Should return the token
        github_token = await token_store.get_github_token("test_user")
        assert github_token == "gh_token_123"
    
    @pytest.mark.asyncio
    async def test_get_github_token_expired(self, token_store):
        """Test getting expired GitHub token."""
        user_tokens = UserTokens(
            user_id="test_user",
            github_access_token="gh_token_123",
            github_expires_at=time.time() - 3600  # Expired
        )
        
        await token_store.store_user_tokens(user_tokens)
        
        # Should return None for expired token
        github_token = await token_store.get_github_token("test_user")
        assert github_token is None
    
    @pytest.mark.asyncio
    async def test_get_github_token_no_token(self, token_store):
        """Test getting GitHub token when none exists."""
        user_tokens = UserTokens(user_id="test_user")  # No GitHub token
        
        await token_store.store_user_tokens(user_tokens)
        
        github_token = await token_store.get_github_token("test_user")
        assert github_token is None
    
    @pytest.mark.asyncio
    async def test_update_github_token(self, token_store):
        """Test updating GitHub token for user."""
        # Initial user with no GitHub token
        user_tokens = UserTokens(user_id="test_user")
        await token_store.store_user_tokens(user_tokens)
        
        # Update GitHub token
        await token_store.update_github_token(
            user_id="test_user",
            access_token="new_gh_token_456",
            refresh_token="new_gh_refresh_789",
            expires_in=7200
        )
        
        # Verify update
        updated_tokens = await token_store.get_user_tokens("test_user")
        assert updated_tokens.github_access_token == "new_gh_token_456"
        assert updated_tokens.github_refresh_token == "new_gh_refresh_789"
        assert updated_tokens.github_expires_at is not None
    
    @pytest.mark.asyncio
    async def test_update_github_token_new_user(self, token_store):
        """Test updating GitHub token for new user."""
        # Update GitHub token for non-existent user (should create new entry)
        await token_store.update_github_token(
            user_id="new_user",
            access_token="gh_token_123",
            expires_in=3600
        )
        
        # Verify user was created
        user_tokens = await token_store.get_user_tokens("new_user")
        assert user_tokens is not None
        assert user_tokens.github_access_token == "gh_token_123"
    
    @pytest.mark.asyncio
    async def test_update_oauth_token(self, token_store):
        """Test updating OAuth token for user."""
        # Update OAuth token
        await token_store.update_oauth_token(
            user_id="test_user",
            access_token="oauth_token_123",
            refresh_token="oauth_refresh_456",
            expires_in=1800
        )
        
        # Verify update
        user_tokens = await token_store.get_user_tokens("test_user")
        assert user_tokens.oauth_access_token == "oauth_token_123"
        assert user_tokens.oauth_refresh_token == "oauth_refresh_456"
        assert user_tokens.oauth_expires_at is not None
    
    @pytest.mark.asyncio
    async def test_delete_user_tokens(self, token_store):
        """Test deleting user tokens."""
        user_tokens = UserTokens(user_id="test_user", github_access_token="token")
        await token_store.store_user_tokens(user_tokens)
        
        # Verify user exists
        assert await token_store.get_user_tokens("test_user") is not None
        
        # Delete user tokens
        result = await token_store.delete_user_tokens("test_user")
        assert result is True
        
        # Verify user is deleted
        assert await token_store.get_user_tokens("test_user") is None
        
        # Try to delete again
        result = await token_store.delete_user_tokens("test_user")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_users(self, token_store):
        """Test listing users with stored tokens."""
        # Initially no users
        users = await token_store.list_users()
        assert len(users) == 0
        
        # Add some users
        user1_tokens = UserTokens(user_id="user1", github_access_token="token1")
        user2_tokens = UserTokens(user_id="user2", github_access_token="token2")
        
        await token_store.store_user_tokens(user1_tokens)
        await token_store.store_user_tokens(user2_tokens)
        
        # List users
        users = await token_store.list_users()
        assert len(users) == 2
        assert "user1" in users
        assert "user2" in users
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, token_store):
        """Test cleaning up expired tokens."""
        current_time = time.time()
        
        # Create users with mixed token states
        user1 = UserTokens(
            user_id="user1",
            github_expires_at=current_time - 3600,  # Expired
            oauth_expires_at=current_time - 1800   # Expired
        )
        
        user2 = UserTokens(
            user_id="user2", 
            github_expires_at=current_time + 3600,  # Valid
            oauth_expires_at=current_time - 1800   # Expired
        )
        
        user3 = UserTokens(
            user_id="user3",
            github_expires_at=current_time + 3600,  # Valid
            oauth_expires_at=current_time + 1800   # Valid
        )
        
        await token_store.store_user_tokens(user1)
        await token_store.store_user_tokens(user2)
        await token_store.store_user_tokens(user3)
        
        # Cleanup expired tokens
        cleaned_count = await token_store.cleanup_expired_tokens()
        
        # Only user1 should be cleaned up (both tokens expired)
        assert cleaned_count == 1
        
        # Verify remaining users
        remaining_users = await token_store.list_users()
        assert len(remaining_users) == 2
        assert "user1" not in remaining_users
        assert "user2" in remaining_users
        assert "user3" in remaining_users
    
    @pytest.mark.asyncio
    async def test_file_path_sanitization(self, token_store):
        """Test user ID sanitization for file paths."""
        # Test with special characters that should be sanitized
        user_id_with_special_chars = "user@domain.com/test"
        user_tokens = UserTokens(user_id=user_id_with_special_chars)
        
        # Should not raise exception
        await token_store.store_user_tokens(user_tokens)
        
        # Should be retrievable
        retrieved = await token_store.get_user_tokens(user_id_with_special_chars)
        assert retrieved is not None
        assert retrieved.user_id == user_id_with_special_chars


if __name__ == "__main__":
    pytest.main([__file__])