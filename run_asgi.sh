#!/bin/sh

set -e

# Run ASGI server with HTTPS using TLS certificates
uvicorn fastmcpv2_example:app \
    --host 127.0.0.1 \
    --port 8080
#    --ssl-keyfile tls_data/server.key \
#    --ssl-certfile tls_data/server.crt

