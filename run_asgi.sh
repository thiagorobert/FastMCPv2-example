#!/bin/sh

set -e

# Run ASGI server with HTTPS using TLS certificates
uvicorn fastmcpv2_example:app \
    --host 0.0.0.0 \
    --port 8443 \
    --ssl-keyfile tls_data/server.key \
    --ssl-certfile tls_data/server.crt

