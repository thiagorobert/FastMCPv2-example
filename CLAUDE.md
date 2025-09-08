# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

### Core Components

**FastMCP Server (`mcp_server.py`)**
- Built on FastMCP v2 framework for creating MCP (Model Context Protocol) servers
- Provides GitHub API integration via OAuth token authentication
- Exposes 3 main MCP tools: `list_repositories`, `get_repository_info`, `get_user_info`
- Dual transport support: stdio (for MCP clients) and HTTPS/ASGI (web API)
- HTTPS support with TLS certificates from `tls_data/` directory
- Configurable auth provider support: Auth0 (default), Keycloak, or Local OAuth server via `AUTH_PROVIDER` environment variable

**Auth Provider Module (`auth_provider.py`)**
- Abstracted OAuth authentication logic for Auth0, Keycloak, and Local OAuth providers
- Factory pattern for creating appropriate auth providers based on configuration
- Centralized OAuth metadata URL generation

**Local OAuth Server (`local_auth_server.py`)**
- Full OAuth 2.1 compliant authorization server for local development and testing
- JWT access token generation with RS256 signing
- Dynamic Client Registration (RFC 7591) support
- PKCE (RFC 7636) implementation with S256 method
- Resource Indicators and Authorization Server Metadata (RFC 8414) support
- Multiple key export formats: JWKS, single JWK, and PEM for testing tools like jwt.io

**GitHub API Module (`github_api.py`)**
- GitHub API integration with token handling and HTTP client management
- Environment variable-based token loading with python-dotenv support
- API request functions with error handling

**Authentication Flow**
- Triple OAuth provider support: Auth0 (default), Keycloak, and Local OAuth server
- Provider selection via `AUTH_PROVIDER` environment variable (`auth0`, `keycloak`, `local`)
- GitHub API access via token-based authentication using `GITHUB_ACCESS_TOKEN` environment variable
- Environment variables loaded from `.env` file via python-dotenv support
- Token loaded via `github_api.load_token()` function at tool execution time

**MCP Tools Architecture**
- Each tool follows pattern: authenticate → make API request → format response
- Common error handling via `make_github_request()` helper function
- All tools return formatted strings (not structured data)

### Key Files

- `mcp_server.py`: Main MCP server implementation
- `auth_provider.py`: Abstracted OAuth authentication logic for Auth0, Keycloak, and Local providers
- `local_auth_server.py`: Local OAuth 2.1 compliant authorization server for development and testing
- `github_api.py`: GitHub API integration with token handling and HTTP client management
- `test_mcp_server.py`: Comprehensive unit tests using FastMCP's in-memory testing
- `test_local_auth_server.py`: Comprehensive unit tests for the local OAuth server (99% coverage)
- `client.py`: RFC 7591-compliant OAuth client for testing dynamic client registration
- `mcp_config.json`: MCP client configuration for testing with Claude CLI
- `.env`: Environment variables file (contains sensitive tokens)
- `run_asgi.sh`: HTTPS/HTTP server startup script with auth provider selection
- `start_mcp_inspector.sh`: MCP Inspector startup script for debugging
- `tls_data/`: Directory containing TLS certificate (`server.crt`) and private key (`server.key`)
- `docs/`: Documentation directory with Auth0 and Keycloak RFC 7591 setup guides
  - `auth0-rfc7591.md`: Auth0 setup guide for RFC 7591 dynamic client registration
  - `keycloak-rfc7591.md`: Keycloak setup guide for RFC 7591 dynamic client registration

### Testing Strategy

Uses FastMCP's [in-memory testing](https://gofastmcp.com/deployment/testing) approach via `Client(mcp)` for zero-overhead testing:
- No network calls or server deployment needed
- Direct tool invocation testing
- Comprehensive mocking of GitHub API responses
- 97% test coverage with only HTTP endpoint and main entry point uncovered

### MCP Integration

The server can be consumed by MCP clients (like Claude) using the configuration in `mcp_config.json`. The test script `test_mcp_using_claude.sh` demonstrates integration with Claude CLI, forcing tool usage with specific prompts to avoid Claude bypassing the MCP.

### Environment Setup

The server requires a `GITHUB_ACCESS_TOKEN` environment variable for GitHub API access. Create a `.env` file in the project root:

```
GITHUB_ACCESS_TOKEN=your_github_personal_access_token_here
KEYCLOAK_INITIAL_ACCESS_TOKEN=your_keycloak_token_here  # Only needed for Keycloak testing
```

### Dependencies

Key dependencies from `pyproject.toml`:
- `fastmcp>=2.11.3`: FastMCP v2 framework
- `httpx>=0.28.1`: HTTP client for GitHub API requests
- `python-dotenv>=1.1.1`: Environment variable loading from .env files
- `uvicorn[standard]>=0.35.0`: ASGI server for HTTP/HTTPS endpoints

## Development Commands

### Unit testing
- Run all tests: `uv run pytest`
- Run MCP server tests: `uv run pytest test_mcp_server.py`
- Run OAuth server tests: `uv run pytest test_local_auth_server.py`
- Run specific test: `uv run pytest test_mcp_server.py::TestFastMCPv2Example::test_load_token_success`
- Run with coverage: `uv run pytest test_mcp_server.py --cov=mcp_server --cov-report=term-missing`
- Run OAuth tests with coverage: `uv run pytest test_local_auth_server.py --cov=local_auth_server --cov-report=term-missing`

### Code Quality
- Lint code: `uv run ruff check .`
- Auto-fix lint issues: `uv run ruff check . --fix`
- Check for dead code: `uv run vulture .`

### Running the MCP server
- MCP server (stdio): `uv run mcp_server.py`
- HTTP server: `./run_asgi.sh --http` 
- HTTPS server: `./run_asgi.sh --https` (default)
- With Keycloak auth: `./run_asgi.sh --auth-provider keycloak`
- HTTP with Keycloak: `./run_asgi.sh --http --auth-provider keycloak`
- With Local OAuth: `./run_asgi.sh --auth-provider local`
- HTTP with Local OAuth: `./run_asgi.sh --http --auth-provider local`

### Running the Local OAuth Server

- Local OAuth server: `uv run python local_auth_server.py`
- Runs on port 8001 by default
- Provides OAuth 2.1 endpoints including JWT token generation
- Includes debug endpoints for testing: `/publickey` (PEM), `/jwk` (single JWK), `/.well-known/jwks.json`

### Running the client

- `uv run client.py`
- Creates a dynamic client, performs OAuth, and calls the MCP server
- Works with any configured auth provider (Auth0, Keycloak, or Local)

### Local OAuth Development Workflow

For local development and testing:

1. **Start Local OAuth Server**: `uv run python local_auth_server.py` (runs on port 8001)
2. **Start MCP Server with Local Auth**: `./run_asgi.sh --http --auth-provider local` (runs on port 8080)
3. **Run Client**: `uv run client.py` (connects to both servers)

The local OAuth server provides JWT tokens that the MCP server validates using the JWKS endpoint at `http://localhost:8001/.well-known/jwks.json`.

## Directives for Claude

**Code Quality Checks (MANDATORY after any code changes):**

1. **Lint Check**: Run `uv run ruff check .` and fix all issues with `uv run ruff check . --fix`
   * DO NOT lint check files under `.venv`

2. **Test Validation**: Run `uv run pytest` to ensure all tests pass

3. **Dead Code Detection**: Run `uv run vulture .` and ask if flagged dead code should be removed

4. **Whitespace Cleanup**: Run `find . -name "*.py" -not -path "./.venv/*" -exec sed -i 's/[[:space:]]*$//' {} \;` to remove trailing whitespaces
   * Verify with: `find . -name "*.py" -not -path "./.venv/*" -exec grep -Hn '[[:space:]]$' {} \;` (should return nothing)

5. **Tab Replacement**: Run `find . -name "*.py" -not -path "./.venv/*" -exec sed -i 's/\t/    /g' {} \;` to replace tabs with 4 spaces

6. **Newline Check**: Ensure all files end with a newline character

**Execute these checks in the exact order listed above before considering any code task complete.**