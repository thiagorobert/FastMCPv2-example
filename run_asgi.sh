#!/bin/sh

set -e

# Default values
PROTOCOL="https"
AUTH_PROVIDER=""

# Parse arguments
while [ $# -gt 0 ]; do
    case $1 in
        --http|http)
            PROTOCOL="http"
            shift
            ;;
        --https|https)
            PROTOCOL="https"
            shift
            ;;
        --auth-provider)
            AUTH_PROVIDER="$2"
            shift 2
            ;;
        --auth-provider=*)
            AUTH_PROVIDER="${1#*=}"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [PROTOCOL] [AUTH_OPTIONS]"
            echo ""
            echo "PROTOCOL:"
            echo "  http, --http       Run HTTP server on port 8080"
            echo "  https, --https     Run HTTPS server on port 8080 (default)"
            echo ""
            echo "AUTH_OPTIONS:"
            echo "  --auth-provider PROVIDER    Set auth provider (auth0|keycloak)"
            echo ""
            echo "Examples:"
            echo "  $0                          # HTTPS with default auth provider"
            echo "  $0 http                     # HTTP with default auth provider"
            echo "  $0 --auth-provider keycloak # HTTPS with Keycloak"
            echo "  $0 http --auth-provider keycloak # HTTP with Keycloak"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set auth provider environment variable if specified
if [ -n "$AUTH_PROVIDER" ]; then
    export AUTH_PROVIDER="$AUTH_PROVIDER"
    echo "Using auth provider: $AUTH_PROVIDER"
fi

if [ "$PROTOCOL" = "https" ]; then
    echo "Starting HTTPS server on port 8080..."
    uvicorn fastmcpv2_example:app \
        --host 127.0.0.1 \
        --port 8080 \
        --ssl-keyfile tls_data/server.key \
        --ssl-certfile tls_data/server.crt
else
    echo "Starting HTTP server on port 8080..."
    uvicorn fastmcpv2_example:app \
        --host 127.0.0.1 \
        --port 8080
fi

