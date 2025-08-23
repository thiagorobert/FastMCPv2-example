import pytest
import json
import tempfile
import os
from unittest.mock import AsyncMock, patch, mock_open, MagicMock
from fastmcp import Client
from fastmcpv2_example import mcp, make_github_request, load_token


class TestFastMCPv2Example:
    """Test suite for FastMCPv2 GitHub OAuth example using in-memory testing."""

    @pytest.fixture
    def mock_token_file(self):
        """Create a mock token file for testing."""
        token_data = {"access_token": "test_token_123"}
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(token_data, f)
            return f.name

    @pytest.fixture
    def mock_github_api_response(self):
        """Mock GitHub API response data."""
        return {
            "user_repos": [
                {
                    "full_name": "testuser/test-repo",
                    "description": "A test repository",
                    "language": "Python",
                    "stargazers_count": 42,
                    "private": False,
                    "html_url": "https://github.com/testuser/test-repo"
                }
            ],
            "repo_info": {
                "full_name": "testuser/test-repo",
                "description": "A test repository",
                "language": "Python",
                "stargazers_count": 42,
                "forks_count": 5,
                "open_issues_count": 2,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-12-01T00:00:00Z",
                "private": False,
                "html_url": "https://github.com/testuser/test-repo",
                "clone_url": "https://github.com/testuser/test-repo.git"
            },
            "user_info": {
                "login": "testuser",
                "name": "Test User",
                "email": "test@example.com",
                "bio": "Test bio",
                "location": "Test City",
                "public_repos": 10,
                "followers": 50,
                "following": 25,
                "html_url": "https://github.com/testuser"
            }
        }

    def test_load_token_success(self, mock_token_file):
        """Test successful token loading."""
        with patch('fastmcpv2_example.TOKEN_FILE', mock_token_file):
            token = load_token()
            assert token == "test_token_123"
        
        # Clean up
        os.unlink(mock_token_file)

    def test_load_token_missing_access_token(self):
        """Test token loading with missing access_token key."""
        invalid_token_data = {"invalid_key": "value"}
        mock_file_content = json.dumps(invalid_token_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with pytest.raises(RuntimeError, match="Github access token expected"):
                load_token()

    @pytest.mark.asyncio
    async def test_make_github_request_success(self):
        """Test successful GitHub API request."""
        mock_response_data = {"test": "data"}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            # Create mock response
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            
            # Create mock client instance
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            
            # Set up the async context manager
            mock_client_context = AsyncMock()
            mock_client_context.__aenter__.return_value = mock_client_instance
            mock_client_context.__aexit__.return_value = None
            mock_client_class.return_value = mock_client_context
            
            result = await make_github_request("https://api.github.com/test", "test_token")
            assert result == mock_response_data

    @pytest.mark.asyncio
    async def test_make_github_request_failure(self):
        """Test GitHub API request failure."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            result = await make_github_request("https://api.github.com/test", "test_token")
            assert result is None

    @pytest.mark.asyncio
    async def test_list_repositories_tool(self, mock_token_file, mock_github_api_response):
        """Test list_repositories tool using in-memory testing."""
        with patch('fastmcpv2_example.TOKEN_FILE', mock_token_file):
            with patch('fastmcpv2_example.make_github_request') as mock_request:
                mock_request.return_value = mock_github_api_response["user_repos"]
                
                # Use in-memory testing with FastMCP Client
                async with Client(mcp) as client:
                    result = await client.call_tool("list_repositories", {})
                    
                    assert "testuser/test-repo" in result.data
                    assert "A test repository" in result.data
                    assert "Python" in result.data
                    assert "42" in result.data
        
        # Clean up
        os.unlink(mock_token_file)

    @pytest.mark.asyncio
    async def test_list_repositories_no_data(self, mock_token_file):
        """Test list_repositories tool when no data is returned."""
        with patch('fastmcpv2_example.TOKEN_FILE', mock_token_file):
            with patch('fastmcpv2_example.make_github_request') as mock_request:
                mock_request.return_value = None
                
                async with Client(mcp) as client:
                    result = await client.call_tool("list_repositories", {})
                    assert result.data == "Unable to fetch repositories."
        
        # Clean up
        os.unlink(mock_token_file)

    @pytest.mark.asyncio
    async def test_get_repository_info_tool(self, mock_token_file, mock_github_api_response):
        """Test get_repository_info tool using in-memory testing."""
        with patch('fastmcpv2_example.TOKEN_FILE', mock_token_file):
            with patch('fastmcpv2_example.make_github_request') as mock_request:
                mock_request.return_value = mock_github_api_response["repo_info"]
                
                async with Client(mcp) as client:
                    result = await client.call_tool("get_repository_info", {
                        "owner": "testuser",
                        "repo": "test-repo"
                    })
                    
                    assert "testuser/test-repo" in result.data
                    assert "A test repository" in result.data
                    assert "Forks: 5" in result.data
                    assert "Issues: 2" in result.data
        
        # Clean up
        os.unlink(mock_token_file)

    @pytest.mark.asyncio
    async def test_get_repository_info_no_data(self, mock_token_file):
        """Test get_repository_info tool when no data is returned."""
        with patch('fastmcpv2_example.TOKEN_FILE', mock_token_file):
            with patch('fastmcpv2_example.make_github_request') as mock_request:
                mock_request.return_value = None
                
                async with Client(mcp) as client:
                    result = await client.call_tool("get_repository_info", {
                        "owner": "testuser",
                        "repo": "test-repo"
                    })
                    assert "Unable to fetch information for repository testuser/test-repo." in result.data
        
        # Clean up
        os.unlink(mock_token_file)

    @pytest.mark.asyncio
    async def test_get_user_info_tool(self, mock_token_file, mock_github_api_response):
        """Test get_user_info tool using in-memory testing."""
        with patch('fastmcpv2_example.TOKEN_FILE', mock_token_file):
            with patch('fastmcpv2_example.make_github_request') as mock_request:
                mock_request.return_value = mock_github_api_response["user_info"]
                
                async with Client(mcp) as client:
                    result = await client.call_tool("get_user_info", {})
                    
                    assert "Username: testuser" in result.data
                    assert "Name: Test User" in result.data
                    assert "Email: test@example.com" in result.data
                    assert "Public Repos: 10" in result.data
        
        # Clean up
        os.unlink(mock_token_file)

    @pytest.mark.asyncio
    async def test_get_user_info_no_data(self, mock_token_file):
        """Test get_user_info tool when no data is returned."""
        with patch('fastmcpv2_example.TOKEN_FILE', mock_token_file):
            with patch('fastmcpv2_example.make_github_request') as mock_request:
                mock_request.return_value = None
                
                async with Client(mcp) as client:
                    result = await client.call_tool("get_user_info", {})
                    assert result.data == "Unable to fetch user information."
        
        # Clean up
        os.unlink(mock_token_file)

    @pytest.mark.asyncio
    async def test_tools_with_authentication_failure(self):
        """Test tools behavior when token loading fails."""
        with patch('fastmcpv2_example.load_token') as mock_load_token:
            mock_load_token.side_effect = RuntimeError("Token file not found")
            
            async with Client(mcp) as client:
                # Test list_repositories - should raise RuntimeError due to token failure
                try:
                    await client.call_tool("list_repositories", {})
                    assert False, "Expected RuntimeError to be raised"
                except Exception as e:
                    assert "Token file not found" in str(e)
                
                # Test get_repository_info - should raise RuntimeError due to token failure
                try:
                    await client.call_tool("get_repository_info", {
                        "owner": "testuser",
                        "repo": "test-repo"
                    })
                    assert False, "Expected RuntimeError to be raised"
                except Exception as e:
                    assert "Token file not found" in str(e)
                
                # Test get_user_info - should raise RuntimeError due to token failure
                try:
                    await client.call_tool("get_user_info", {})
                    assert False, "Expected RuntimeError to be raised"
                except Exception as e:
                    assert "Token file not found" in str(e)


if __name__ == "__main__":
    pytest.main([__file__])