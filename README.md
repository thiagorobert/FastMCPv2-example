# FastMCP + OAuth 2.1 Dynamic Client Registration Demo

A hands-on exploration of modern authentication patterns with **MCP (Model Context Protocol)** using [FastMCP v2](https://github.com/jlowin/fastmcp), **Dynamic Client Registration (RFC 7591)**, and multiple **OAuth 2.1 authorization servers**.

## What You'll Learn

### 🔌 **MCP (Model Context Protocol)**
- Build MCP servers that can be consumed by AI assistants like Claude
- Implement dual transport modes: stdio for MCP clients and HTTP/HTTPS for web APIs

### 🔐 **Dynamic Client Registration (RFC 7591)**
- Register OAuth clients programmatically without manual setup
- Implement PKCE (Proof Key for Code Exchange) for enhanced security
- Generate and validate JWT access tokens with RS256 signing

### 🏢 **Multiple OAuth Provider Integration**
Compare and contrast three different authorization server approaches:
- **Auth0** - Enterprise identity platform
- **Keycloak** - Open-source identity management
- **Local OAuth Server** - Custom OAuth 2.1 implementation for development

## Architecture Overview

**NEW: OAuth Proxy Pattern with Dynamic Token Management**

```
┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │      Auth Provider      │    │   MCP Server    │    │   GitHub API    │
│   (client.py)   │    │ (Auth0/Keycloak/Local)  │    │ (mcp_server.py) │    │                 │
└─────────────────┘    └─────────────────────────┘    └─────────────────┘    └─────────────────┘
         │                          │                          │                          │
         │ 1. Dynamic Client        │                          │                          │
         │    Registration          │                          │                          │
         │─────────────────────────►│                          │                          │
         │                          │                          │                          │
         │ 2. OAuth Flow with       │                          │                          │
         │    GitHub Scope          │                          │                          │
         │◄────────────────────────►│                          │                          │
         │                          │                          │                          │
         │                          │ 3. Store GitHub tokens   │                          │
         │                          │    per user              │                          │
         │                          │─────────────────────────►│                          │
         │                                                     │                          │
         │ 4. Authenticated MCP calls (with JWT)               │                          │
         │────────────────────────────────────────────────────►│                          │
         │                                                     │                          │
         │                                                     │ 5. Use user's GitHub    │
         │                                                     │    token dynamically    │
         │                                                     │─────────────────────────►│
```

**Key Innovation**: No more pre-configured `GITHUB_ACCESS_TOKEN`! The system now:
1. Captures GitHub tokens during OAuth social login
2. Stores tokens per authenticated user
3. Dynamically retrieves the correct token for each API call

## Quick Start

### 1. Setup
```bash
git clone https://github.com/thiagorobert/FastMCPv2-example.git
cd FastMCPv2-example
uv sync

# Patch .venv
./apply_venv_patch.sh

# Configure environment (optional - only needed for fallback mode)
cp .env.example .env
# Edit .env and set GITHUB_ACCESS_TOKEN (optional - used as fallback only)
```

**Note**: `GITHUB_ACCESS_TOKEN` is now **optional**! The system will obtain GitHub tokens dynamically through OAuth social login. The environment token is only used as a fallback when no user-specific token is available.

### 2. Choose Your Learning Path

#### 🚀 **Quickest Start - Local OAuth**
Experience the full flow with zero external dependencies and **dynamic GitHub token management**:
```bash
# Terminal 1: Start local OAuth server with GitHub social simulation
uv run python local_auth_server.py

# Terminal 2: Start MCP server (no GITHUB_ACCESS_TOKEN needed!)
./run_asgi.sh --auth-provider local

# Terminal 3: Run OAuth client demo with GitHub scope
uv run client.py
```

**New in this version**: The MCP server no longer requires pre-configuration with `GITHUB_ACCESS_TOKEN`. Instead, GitHub access tokens are obtained dynamically during the OAuth flow and stored per-user!

#### 🏢 **Enterprise Setup - Auth0**
Learn production-ready identity management:
```bash
# Follow setup guide
cat docs/auth0-rfc7591.md

# Terminal 1: Start with Auth0 provider
./run_asgi.sh --auth-provider auth0

# Terminal 2: Run OAuth client demo
uv run client.py
```

#### 🔧 **Self-Hosted Setup - Keycloak**
Explore open-source identity solutions:
```bash
# Terminal 1: Start Keycloak with Docker
docker run -p 8081:8080 -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:24.0.4 start-dev

# Follow setup guide
cat docs/keycloak-rfc7591.md

# Terminal 2: Start with Keycloak provider
./run_asgi.sh --auth-provider keycloak

# Terminal 3: Run OAuth client demo
uv run client.py
```

### 3. Test MCP Integration using Claude CLI
Test direct MCP invocation from Claude CLI:
```bash
# Use with Claude CLI or other MCP clients
./test_mcp_using_claude.sh
```
In this flow there is no Dynamic Client Registration or OAuth authentication. Claude CLI runs the MCP server and connects to it via `stdio` transport.

## Key Learning Components

### 📁 **Core Files**
- **`mcp_server.py`** - FastMCP server with configurable OAuth providers and dynamic token lookup
- **`local_auth_server.py`** - Complete OAuth 2.1 server with GitHub social connection simulation
- **`client.py`** - RFC 7591 dynamic client registration with GitHub scope request
- **`auth_provider.py`** - Provider abstraction layer
- **`user_token_store.py`** - **NEW**: User-specific GitHub token storage and management
- **`github_api.py`** - **ENHANCED**: Dynamic token selection based on authenticated user

### 📖 **Documentation**
- **`docs/auth0-rfc7591.md`** - Auth0 configuration walkthrough
- **`docs/keycloak-rfc7591.md`** - Keycloak setup instructions

## Exploring the Code

### Dynamic Client Registration + GitHub Token Flow
```python
# 1. Register client dynamically with GitHub scope (client.py)
client_data = {
    "client_name": "My Dynamic App",
    "redirect_uris": ["http://127.0.0.1:8082/callback"]
}

# 2. OAuth flow with PKCE + GitHub scope
authorization_url = f"{auth_server}/oauth/authorize"
params = {
    "scope": "github:user",  # Request GitHub access
    "code_challenge": code_challenge,
    "code_challenge_method": "S256"
}

# 3. User authenticates with GitHub (simulated in local server)
# 4. Exchange code for JWT token + GitHub token stored automatically
token_response = await client.post("/oauth/token", data={
    "grant_type": "authorization_code",
    "code": auth_code,
    "code_verifier": code_verifier
})
```

### Enhanced MCP Tool Implementation
```python
@mcp.tool()
async def list_repositories() -> str:
    """List GitHub repositories with dynamic user token lookup."""
    # Automatically gets user ID from JWT context
    user_id = get_current_user_id()
    
    # Uses user's specific GitHub token, falls back to env token
    return await github_api.list_repositories(user_id)
```

## Learning Outcomes

After exploring this repository, you'll understand:

✅ **MCP Integration** - How to build servers that AI assistants can consume  
✅ **OAuth 2.1 Security** - PKCE, JWT tokens, and authorization flows  
✅ **Dynamic Registration** - Programmatic client creation across providers  
✅ **Provider Comparison** - Trade-offs between Auth0, Keycloak, and custom solutions  
✅ **OAuth Proxy Pattern** - **NEW**: How to eliminate pre-configured API tokens  
✅ **Token Management** - **NEW**: Per-user token storage and dynamic lookup  
✅ **Social Login Integration** - **NEW**: Capturing third-party tokens during OAuth flow  

## Next Steps

- Experiment with different OAuth scopes and permissions
- Add additional MCP tools for other APIs
- Implement token refresh and revocation flows
- Explore Auth0 Rules or Keycloak custom authenticators
- Deploy the local OAuth server as a reusable microservice
- ~~Can OAuth Token Exchange (rfc8693) be used to avoid having to preconfigure the MCP Server with a Github access token?~~ **✅ SOLVED: Implemented OAuth Proxy Pattern with dynamic token management!**

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [RFC 7591 - OAuth 2.0 Dynamic Client Registration](https://tools.ietf.org/html/rfc7591)
- [RFC 7636 - PKCE](https://tools.ietf.org/html/rfc7636)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)