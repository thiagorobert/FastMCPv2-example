#!/bin/sh

set -e

uvicorn fastmcpv2_example:app --host 0.0.0.0 --port 8080

