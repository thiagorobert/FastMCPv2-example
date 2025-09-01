#!/bin/sh

set -e

patch -p0 < mcp_keycloak_auth_changes.patch

