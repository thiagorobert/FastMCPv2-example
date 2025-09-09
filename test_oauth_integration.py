#!/usr/bin/env python3
"""
Test OAuth integration to verify GitHub token storage.
"""

import asyncio
from user_token_store import token_store


async def test_oauth_integration():
    """Test that OAuth flow stored GitHub tokens correctly."""
    print("🔍 Testing OAuth Integration - Checking stored tokens...")
    print("=" * 60)
    
    # List all users with stored tokens
    users = await token_store.list_users()
    print(f"Found {len(users)} users with stored tokens:")
    
    if not users:
        print("❌ No users found. OAuth flow may not have completed successfully.")
        return
    
    for user in users:
        print(f"\n👤 User: {user}")
        
        # Get user tokens
        user_tokens = await token_store.get_user_tokens(user)
        if user_tokens:
            print(f"   GitHub Token: {'✅ Present' if user_tokens.github_access_token else '❌ Missing'}")
            print(f"   GitHub Refresh: {'✅ Present' if user_tokens.github_refresh_token else '❌ Missing'}")
            print(f"   OAuth Token: {'✅ Present' if user_tokens.oauth_access_token else '❌ Missing'}")
            print(f"   GitHub Expired: {'❌ Yes' if user_tokens.is_github_token_expired() else '✅ No'}")
            print(f"   OAuth Expired: {'❌ Yes' if user_tokens.is_oauth_token_expired() else '✅ No'}")
            
            # Test dynamic token lookup
            github_token = await token_store.get_github_token(user)
            if github_token:
                print(f"   Dynamic Lookup: ✅ Success - {github_token[:20]}...")
                print(f"   🎉 OAuth Proxy Pattern working correctly!")
            else:
                print(f"   Dynamic Lookup: ❌ Failed")
        else:
            print("   ❌ Failed to retrieve user tokens")
    
    print("\n" + "=" * 60)
    print("✨ OAuth Integration Test Complete")


if __name__ == "__main__":
    asyncio.run(test_oauth_integration())