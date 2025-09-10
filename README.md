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

```
┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────┐
│   MCP Client    │    │      Auth Provider      │    │   MCP Server    │
│   (client.py)   │    │ (Auth0/Keycloak/Local)  │    │ (mcp_server.py) │
└─────────────────┘    └─────────────────────────┘    └─────────────────┘
         │                          │                          │
         │ 1. Dynamic Client        │                          │
         │     Registration         │                          │
         │─────────────────────────►│                          │
         │                          │                          │
         │ 2. OAuth Flow            │                          │
         │◄────────────────────────►│                          │
         │                                                     │
         │                                                     │
         │ 3. Authenticated calls to MCP Tools                 │
         │            (with JWT)                               │
         │────────────────────────────────────────────────────►│
```

## Quick Start

### 1. Setup
```bash
git clone https://github.com/thiagorobert/FastMCPv2-example.git
cd FastMCPv2-example
uv sync

# Patch .venv
./apply_venv_patch.sh

# Configure environment
cp .env.example .env
# Edit .env and set GITHUB_ACCESS_TOKEN
```

### 2. Choose Your Learning Path

#### 🚀 **Quickest Start - Local OAuth**
Experience the full flow with zero external dependencies:
```bash
# Terminal 1: Start local OAuth server
uv run python local_auth_server.py

# Terminal 2: Start MCP server  
./run_asgi.sh --auth-provider local

# Terminal 3: Run OAuth client demo
uv run client.py
```

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
- **`mcp_server.py`** - FastMCP server with configurable OAuth providers
- **`local_auth_server.py`** - Complete OAuth 2.1 server implementation  
- **`client.py`** - RFC 7591 dynamic client registration example
- **`auth_provider.py`** - Provider abstraction layer

### 📖 **Documentation**
- **`docs/auth0-rfc7591.md`** - Auth0 configuration walkthrough
- **`docs/keycloak-rfc7591.md`** - Keycloak setup instructions

## Exploring the Code

### Dynamic Client Registration Flow
```python
# 1. Register client dynamically (client.py)
client_data = {
    "client_name": "My Dynamic App",
    "redirect_uris": ["http://127.0.0.1:8082/callback"]
}

# 2. OAuth flow with PKCE
authorization_url = f"{auth_server}/oauth/authorize"
# ... PKCE code challenge generation

# 3. Exchange code for JWT token
token_response = await client.post("/oauth/token", data={
    "grant_type": "authorization_code",
    "code": auth_code,
    "code_verifier": code_verifier
})
```

### MCP Tool Implementation
```python
@mcp.tool()
async def list_repositories() -> str:
    """List GitHub repositories with OAuth authentication."""
    return await github_api.list_repositories()
```

## Learning Outcomes

After exploring this repository, you'll understand:

✅ **MCP Integration** - How to build servers that AI assistants can consume  
✅ **OAuth 2.1 Security** - PKCE, JWT tokens, and authorization flows  
✅ **Dynamic Registration** - Programmatic client creation across providers  
✅ **Provider Comparison** - Trade-offs between Auth0, Keycloak, and custom solutions  

## Next Steps

- Experiment with different OAuth scopes and permissions
- Add additional MCP tools for other APIs
- Implement token refresh and revocation flows
- Explore Auth0 Rules or Keycloak custom authenticators
- Deploy the local OAuth server as a reusable microservice
- Can OAuth Token Exchange (rfc8693) be used to avoid having to preconfigure the MCP Server with a Github access token?

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [RFC 7591 - OAuth 2.0 Dynamic Client Registration](https://tools.ietf.org/html/rfc7591)
- [RFC 7636 - PKCE](https://tools.ietf.org/html/rfc7636)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
   * [Authorization section](https://modelcontextprotocol.io/specification/draft/basic/authorization)
- [An introduction to MCP and Auth](https://auth0.com/blog/an-introduction-to-mcp-and-authorization/)
   * I found this article after implementing the example in this repo, and wish I had found it before (but would likely not have appreciated it as much)
- [Open issue: Treat the MCP as RS rather than AS ](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/205)
   * This proposal is similar to how I implemented the example in this repo
- [MCP Auth](https://mcp-auth.dev/)
   * A library to ease implementation of auth for MCPs, including integration with several providers

### List of Auth providers

* [Okta](https://www.okta.com/)
   * owns Auth0
* [Auth0](https://auth0.com)
* [Keycloak](https://keycloak.org)
* [Frontegg](https://frontegg.com)
* [Descope](https://descope.com)
* [FusionAuth](https://fusionauth.io)
* [WorkOS](https://workos.com)
* [Entra ID](https://www.microsoft.com/en-us/security/business/identity-access/microsoft-entra-id)
* [Stytch](https://stytch.com)
* [Logto](https://logto.io/)
* [WSO2](https://wso2.com)
   * [Asgardeo](https://wso2.com/asgardeo/)
   * [Identity Server](https://wso2.com/identity-server/)