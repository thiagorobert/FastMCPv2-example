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
- Token file loading and validation
- API request functions with error handling

**Authentication Flow**
- Dual OAuth provider support: Auth0 (default) and Keycloak
- Provider selection via `AUTH_PROVIDER` environment variable
- GitHub API access via token-based authentication using `github_token.json` file
- Token loaded via `github_api.load_token()` function at tool execution time

**MCP Tools Architecture**
- Each tool follows pattern: authenticate → make API request → format response
- Common error handling via `make_github_request()` helper function
- All tools return formatted strings (not structured data)

### Key Files

- `fastmcpv2_example.py`: Main MCP server implementation
- `test_fastmcpv2_example.py`: Comprehensive unit tests using FastMCP's in-memory testing
- `mcp_config.json`: MCP client configuration for testing with Claude CLI
- `github_token.json`: GitHub personal access token storage (sensitive)
- `run_asgi.sh`: HTTPS server startup script
- `run_https.py`: Python-based HTTPS server runner with SSL configuration
- `tls_data/`: Directory containing TLS certificate (`server.crt`) and private key (`server.key`)

### Testing Strategy

Uses FastMCP's [in-memory testing](https://gofastmcp.com/deployment/testing) approach via `Client(mcp)` for zero-overhead testing:
- No network calls or server deployment needed
- Direct tool invocation testing
- Comprehensive mocking of GitHub API responses
- 97% test coverage with only HTTP endpoint and main entry point uncovered

### MCP Integration

The server can be consumed by MCP clients (like Claude) using the configuration in `mcp_config.json`. The test script `test_mcp_using_claude.sh` demonstrates integration with Claude CLI, forcing tool usage with specific prompts to avoid Claude bypassing the MCP.

## Development Commands

### Testing
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
- HTTPS server: `./run_asgi.sh --https` 
- With Keycloak auth: `./run_asgi.sh --auth-provider keycloak`
- HTTP with Keycloak: `./run_asgi.sh --http --auth-provider keycloak`
- Set auth provider via env: `AUTH_PROVIDER=keycloak uv run fastmcpv2_example.py`
- Test MCP integration: `./test_mcp_using_claude.sh`

## Directives for Claude

* Always ensure there are not lint errors after code changes
   * DO NOT lint check files under `.venv`
* Always ensure all tests pass after code changes
* Always check for dead code after code changes, ask if the dead code should be removed