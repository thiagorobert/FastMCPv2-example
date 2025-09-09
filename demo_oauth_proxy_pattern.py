#!/usr/bin/env python3
"""
Demo script showing the new OAuth Proxy Pattern functionality.

This script demonstrates:
1. No pre-configured GITHUB_ACCESS_TOKEN required
2. Dynamic GitHub token management per user
3. GitHub social connection simulation through local OAuth
"""

import asyncio
import time
from user_token_store import UserTokenStore, UserTokens


async def demo_token_management():
    """Demonstrate the user token storage system."""
    print("🔐 OAuth Proxy Pattern Demo - Dynamic Token Management")
    print("=" * 60)
    
    # Initialize token store
    token_store = UserTokenStore(".demo_tokens")
    
    # Simulate OAuth flow with GitHub social connection
    print("\n1. Simulating OAuth flow with GitHub social connection...")
    
    # User 1: testuser
    user1_tokens = UserTokens(
        user_id="mcp_client_testuser123",  # This would be the client_id from OAuth
        github_access_token="github_token_for_testuser",
        github_refresh_token="github_refresh_testuser", 
        github_expires_at=time.time() + 3600,  # Valid for 1 hour
        oauth_access_token="jwt_token_for_testuser",
        oauth_expires_at=time.time() + 1800   # Valid for 30 minutes
    )
    
    # User 2: demouser
    user2_tokens = UserTokens(
        user_id="mcp_client_demouser456",
        github_access_token="github_token_for_demouser",
        github_refresh_token="github_refresh_demouser",
        github_expires_at=time.time() + 7200,  # Valid for 2 hours
        oauth_access_token="jwt_token_for_demouser", 
        oauth_expires_at=time.time() + 3600    # Valid for 1 hour
    )
    
    # Store tokens
    await token_store.store_user_tokens(user1_tokens)
    await token_store.store_user_tokens(user2_tokens)
    
    print("   ✅ Stored GitHub tokens for testuser")
    print("   ✅ Stored GitHub tokens for demouser")
    
    # Demonstrate token retrieval
    print("\n2. Demonstrating dynamic token lookup...")
    
    # Get GitHub tokens for each user
    testuser_github_token = await token_store.get_github_token("mcp_client_testuser123")
    demouser_github_token = await token_store.get_github_token("mcp_client_demouser456")
    
    print(f"   📋 testuser GitHub token: {testuser_github_token[:20]}...")
    print(f"   📋 demouser GitHub token: {demouser_github_token[:20]}...")
    
    # Simulate API call routing
    print("\n3. Simulating MCP API calls with dynamic token selection...")
    print("   🔄 User 'testuser' calls list_repositories():")
    print(f"      → Using token: {testuser_github_token[:20]}...")
    print("      → API call: GET /user/repos (with testuser's token)")
    
    print("   🔄 User 'demouser' calls get_user_info():")
    print(f"      → Using token: {demouser_github_token[:20]}...")
    print("      → API call: GET /user (with demouser's token)")
    
    # Show token expiration handling
    print("\n4. Demonstrating token expiration handling...")
    
    # Create an expired token
    expired_user_tokens = UserTokens(
        user_id="mcp_client_expired789",
        github_access_token="expired_github_token",
        github_expires_at=time.time() - 3600  # Expired 1 hour ago
    )
    await token_store.store_user_tokens(expired_user_tokens)
    
    expired_token = await token_store.get_github_token("mcp_client_expired789")
    if expired_token is None:
        print("   ⚠️  Expired user token correctly rejected")
        print("   🔄 System would fall back to environment GITHUB_ACCESS_TOKEN or return auth error")
    
    # Show user management
    print("\n5. User token management...")
    users = await token_store.list_users()
    print(f"   👥 Total users with stored tokens: {len(users)}")
    for user in users:
        user_tokens = await token_store.get_user_tokens(user)
        github_valid = "✅" if not user_tokens.is_github_token_expired() else "❌"
        oauth_valid = "✅" if not user_tokens.is_oauth_token_expired() else "❌"
        print(f"      - {user}: GitHub {github_valid} | OAuth {oauth_valid}")
    
    # Cleanup demo
    print("\n6. Cleanup...")
    cleaned = await token_store.cleanup_expired_tokens()
    print(f"   🧹 Cleaned up {cleaned} expired token sets")
    
    # Delete demo tokens directory
    import shutil
    shutil.rmtree(".demo_tokens", ignore_errors=True)
    print("   🗑️  Removed demo token storage")
    
    print("\n" + "=" * 60)
    print("✨ Demo complete! Key benefits of OAuth Proxy Pattern:")
    print("   • No pre-configured API tokens needed")
    print("   • Per-user token isolation")
    print("   • Automatic token expiration handling") 
    print("   • Secure token storage with cleanup")
    print("   • Fallback to environment tokens when needed")


if __name__ == "__main__":
    asyncio.run(demo_token_management())