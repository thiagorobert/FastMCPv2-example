# FastMCP + OAuth 2.1 Dynamic Client Registration Demo

A hands-on exploration of modern authentication patterns with **MCP (Model Context Protocol)** using [FastMCP v2](https://github.com/jlowin/fastmcp), **Dynamic Client Registration (RFC 7591)**, and multiple **OAuth 2.1 authorization servers**.

## Key Concepts

### 🔌 **MCP (Model Context Protocol)**
MCP enables AI assistants like Claude to securely access external tools and data sources. Instead of hardcoding API integrations, MCP provides a standardized way for AI models to discover and invoke tools dynamically. This demo shows how to build MCP servers with proper OAuth authentication.

### 🔐 **Dynamic Client Registration (RFC 7591)**
Traditional OAuth requires manual client setup through provider dashboards. Dynamic Client Registration eliminates this friction by allowing applications to register OAuth clients programmatically. This is especially powerful for:
- Development environments that need fresh clients
- Multi-tenant applications 
- Automated testing scenarios

### 🛡️ **OAuth 2.1 Security Enhancements**
OAuth 2.1 mandates security best practices that were optional in 2.0:
- **PKCE (Proof Key for Code Exchange)** - Prevents authorization code interception
- **JWT access tokens with RS256** - Cryptographically signed and verifiable
- **Strict redirect URI matching** - Prevents authorization code theft

### 🏢 **Multiple OAuth Provider Integration**
Compare and contrast three different authorization server approaches:
- **Auth0** - Enterprise identity platform
- **Keycloak** - Open-source identity management
- **Local OAuth Server** - Custom OAuth 2.1 implementation for development

## What You'll Learn

✅ **MCP Integration** - Build servers that AI assistants can consume  
✅ **OAuth 2.1 Security** - PKCE, JWT tokens, and authorization flows  
✅ **Dynamic Registration** - Programmatic client creation across providers  
✅ **Provider Trade-offs** - Compare Auth0, Keycloak, and custom solutions

## How It Works

```
┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────┐          ┌─────────────┐
│   MCP Client    │    │      Auth Provider      │    │   MCP Server    │          │    GitHub   │
│   (client.py)   │    │ (Auth0/Keycloak/Local)  │    │ (mcp_server.py) │          │     API     │
└─────────────────┘    └─────────────────────────┘    └─────────────────┘          └─────────────┘
         │                          │                          │                          │
         │ 1. Dynamic Client        │                          │                          │
         │     Registration         │                          │                          │
         │─────────────────────────►│                          │                          │
         │                          │                          │                          │
         │ 2. OAuth Flow            │                          │                          │
         │◄────────────────────────►│                          │                          │
         │                                                     │                          │
         │                                                     │                          │
         │ 3. Authenticated calls to MCP Tools                 │ 4. GitHub API calls      │
         │            (with JWT)                               │ (Personal Access Token)  │
         │────────────────────────────────────────────────────►│─────────────────────────►│
         │                                                     │                          │
```

The demo showcases the complete OAuth 2.1 + MCP integration flow:
1. **Dynamic Registration** - Client registers itself programmatically
2. **PKCE OAuth Flow** - Secure authorization with code challenges  
3. **JWT Authentication** - MCP server validates tokens from auth provider
4. **GitHub API Access** - MCP server uses Personal Access Token to call GitHub API

## Quick Start

### 1. Setup
```bash
git clone https://github.com/thiagorobert/FastMCPv2-example.git
cd FastMCPv2-example
uv sync

# Patch .venv
./scripts/apply_venv_patch.sh

# Configure environment
cp env.example .env
# Edit .env and set GITHUB_ACCESS_TOKEN
```

### 2. Try the Local OAuth Demo

Experience the complete flow with zero external dependencies:

```bash
# Terminal 1: Start local OAuth server
uv run python src/local_auth_server.py

# Terminal 2: Start MCP server with local auth
./scripts/run_asgi.sh --auth-provider local

# Terminal 3: Run the dynamic client registration demo
uv run src/client.py
```

**What happens:**
1. `client.py` registers a new OAuth client dynamically
2. Performs PKCE-enhanced OAuth flow with the local OAuth server
3. Uses the JWT token to call authenticated MCP tools
4. Fetches your GitHub repositories via the MCP server

## Alternative Providers

### 🏢 **Auth0 Setup**
1. Follow the [Auth0 setup guide](docs/auth0-rfc7591.md) to configure your Auth0 environment
2. Run the demo:
```bash
./scripts/run_asgi.sh --auth-provider auth0
uv run src/client.py
```

### 🔧 **Keycloak Setup**
1. Start Keycloak:
```bash
podman run -p 8081:8080 -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:24.0.4 start-dev
```
2. Follow the [Keycloak setup guide](docs/keycloak-rfc7591.md) to configure your Keycloak environment
3. Run the demo:
```bash
./scripts/run_asgi.sh --auth-provider keycloak
uv run src/client.py
```

## Test MCP Integration with Claude CLI
```bash
# Test direct MCP invocation from Claude CLI
./scripts/test_mcp_using_claude.sh
```
*Note: This uses `stdio` transport - no OAuth authentication involved.*

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [RFC 7591 - OAuth 2.0 Dynamic Client Registration](https://tools.ietf.org/html/rfc7591)
- [RFC 7636 - PKCE](https://tools.ietf.org/html/rfc7636)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
  * [Authorization section](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
     * [Auth Server Discovery](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization#authorization-server-discovery)
- [An introduction to MCP and Auth](https://auth0.com/blog/an-introduction-to-mcp-and-authorization/)
  * I found this article after implementing the example in this repo, and I wish I had found it before (but would likely not have appreciated it as much)
- [MCP Auth](https://mcp-auth.dev/)
  * A library to ease implementation of auth for MCPs, including integration with several providers

### List of Auth providers

* [Okta](https://www.okta.com/)
  * which owns Auth0
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