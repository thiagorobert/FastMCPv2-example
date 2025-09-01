# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

### Core Components

**FastMCP Server (`fastmcpv2_example.py`)**
- Built on FastMCP v2 framework for creating MCP (Model Context Protocol) servers
- Provides GitHub API integration via OAuth token authentication
- Exposes 3 main MCP tools: `list_repositories`, `get_repository_info`, `get_user_info`
- Dual transport support: stdio (for MCP clients) and HTTPS/ASGI (web API)
- HTTPS support with TLS certificates from `tls_data/` directory
- Configurable auth provider support: Auth0 (default) or Keycloak via `AUTH_PROVIDER` environment variable

**Auth Provider Module (`auth_provider.py`)**
- Abstracted OAuth authentication logic for Auth0 and Keycloak providers
- Factory pattern for creating appropriate auth providers based on configuration
- Centralized OAuth metadata URL generation

**GitHub API Module (`github_api.py`)**
- GitHub API integration with token handling and HTTP client management
- Environment variable-based token loading with python-dotenv support
- API request functions with error handling

**Authentication Flow**
- Dual OAuth provider support: Auth0 (default) and Keycloak
- Provider selection via `AUTH_PROVIDER` environment variable
- GitHub API access via token-based authentication using `GITHUB_ACCESS_TOKEN` environment variable
- Environment variables loaded from `.env` file via python-dotenv support
- Token loaded via `github_api.load_token()` function at tool execution time

**MCP Tools Architecture**
- Each tool follows pattern: authenticate → make API request → format response
- Common error handling via `make_github_request()` helper function
- All tools return formatted strings (not structured data)

### Key Files

- `fastmcpv2_example.py`: Main MCP server implementation
- `auth_provider.py`: Abstracted OAuth authentication logic for Auth0 and Keycloak providers
- `github_api.py`: GitHub API integration with token handling and HTTP client management
- `test_fastmcpv2_example.py`: Comprehensive unit tests using FastMCP's in-memory testing
- `simple_client.py`: RFC 7591-compliant OAuth client for testing dynamic client registration
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
- Run all tests: `uv run pytest test_fastmcpv2_example.py`
- Run specific test: `uv run pytest test_fastmcpv2_example.py::TestFastMCPv2Example::test_load_token_success`
- Run with coverage: `uv run pytest test_fastmcpv2_example.py --cov=fastmcpv2_example --cov-report=term-missing`

### Code Quality
- Lint code: `uv run ruff check .`
- Auto-fix lint issues: `uv run ruff check . --fix`
- Check for dead code: `uv run vulture .`

### Running the MCP server
- MCP server (stdio): `uv run fastmcpv2_example.py`
- HTTP server: `./run_asgi.sh --http` 
- HTTPS server: `./run_asgi.sh --https` (default)
- With Keycloak auth: `./run_asgi.sh --auth-provider keycloak`
- HTTP with Keycloak: `./run_asgi.sh --http --auth-provider keycloak`

### Running the client

- `uv run simple_client.py`
- creates a dynamic client, performa OAuth, and calls the MCP server

## Directives for Claude

* Always ensure there are not lint errors after code changes
   * DO NOT lint check files under `.venv`
* Always ensure all tests pass after code changes
* Always check for dead code after code changes, ask if the dead code should be removed
* Always ensure there are no trailing whitespaces or tabs in all files
* Replace tabs with spaces in all files
* Always ensure there is a new line at the end of all files