#!/bin/bash

set -e


python -c "
import asyncio
import fastmcpv2_example
print(fastmcpv2_example.GITHUB_CLIENT_ID)
print(fastmcpv2_example.GITHUB_CLIENT_SECRET)
asyncio.run(fastmcpv2_example.authenticate())
print(asyncio.run(fastmcpv2_example.list_repositories()))
"
