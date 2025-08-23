#!/usr/bin/env python3
"""
HTTPS server runner for FastMCP v2 example with TLS configuration.
"""

import uvicorn
from pathlib import Path

def main():
    """Run the HTTPS server."""
    try:
        # Check if certificate files exist
        cert_file = Path("tls_data/server.crt")
        key_file = Path("tls_data/server.key")
        
        if not cert_file.exists():
            raise FileNotFoundError(f"Certificate file not found: {cert_file}")
        if not key_file.exists():
            raise FileNotFoundError(f"Private key file not found: {key_file}")
        
        print("Starting FastMCP v2 HTTPS server...")
        print("Server will be available at: https://0.0.0.0:8443")
        print("Health check endpoint: https://0.0.0.0:8443/health")
        
        uvicorn.run(
            "fastmcpv2_example:app",
            host="0.0.0.0",
            port=8443,
            ssl_keyfile="tls_data/server.key",
            ssl_certfile="tls_data/server.crt",
            log_level="info",
            access_log=True
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure TLS certificate files exist in the tls_data/ directory")
        exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        exit(1)

if __name__ == "__main__":
    main()