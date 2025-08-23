# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
- Run all tests: `uv run pytest test_fastmcpv2_example.py`
- Run specific test: `uv run pytest test_fastmcpv2_example.py::TestFastMCPv2Example::test_load_token_success`
- Run with coverage: `uv run pytest test_fastmcpv2_example.py --cov=fastmcpv2_example --cov-report=term-missing`

### Code Quality
- Lint code: `uv run ruff check .`
- Auto-fix lint issues: `uv run ruff check . --fix`
- Check for dead code: `uv run vulture .`

### Running the Application
- MCP server (stdio): `uv run fastmcpv2_example.py`
- HTTPS server: `./run_asgi.sh` or `python run_https.py` 
- HTTP server (insecure): `uvicorn fastmcpv2_example:app --host 0.0.0.0 --port 8080`
- Test MCP integration: `./test_mcp_using_claude.sh`

### Dependencies
- Add runtime dependency: `uv add <package>`
- Add dev dependency: `uv add --dev <package>`

## Architecture

### Core Components

**FastMCP Server (`fastmcpv2_example.py`)**
- Built on FastMCP v2 framework for creating MCP (Model Context Protocol) servers
- Provides GitHub API integration via OAuth token authentication
- Exposes 3 main MCP tools: `list_repositories`, `get_repository_info`, `get_user_info`
- Dual transport support: stdio (for MCP clients) and HTTPS/ASGI (web API)
- HTTPS support with TLS certificates from `tls_data/` directory

**Authentication Flow**
- Token-based authentication using `github_token.json` file
- No OAuth flow implemented - requires pre-existing GitHub personal access token
- Token loaded via `load_token()` function at tool execution time

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

## Directives for Claude

* Always ensure there are not lint errors after code changes
   * DO NOT lint check files under `.venv`
* Always ensure all tests pass after code changes
* Always check for dead code after code changes, ask if the dead code should be removed