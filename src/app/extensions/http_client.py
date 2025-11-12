"""HTTP client for external API proxying (BlackLab, etc.)."""
from __future__ import annotations

import os
import httpx
from typing import Optional

# Singleton HTTP client for persistent connections and connection pooling
_http_client: Optional[httpx.Client] = None

# Get BLS base URL from environment (required for proxying)
BLS_BASE_URL = os.environ.get("BLS_BASE_URL", "http://localhost:8081/blacklab-server").rstrip("/")


def get_http_client() -> httpx.Client:
    """Get or create singleton httpx.Client with connection pooling to BLS.
    
    Uses BLS_BASE_URL from environment (default: http://localhost:8081/blacklab-server).
    All requests should pass the full path (e.g., "/corapan/hits").
    """
    global _http_client

    if _http_client is None:
        _http_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=5.0,    # Connection timeout (shorter for proxy)
                read=30.0,      # Read timeout (reasonable for search)
                write=5.0,      # Write timeout
                pool=5.0,       # Pool timeout (required in httpx 0.27+)
            ),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
            ),
            http2=False,  # Stick with HTTP/1.1 for compatibility
        )

    return _http_client


def close_http_client() -> None:
    """Close and cleanup singleton HTTP client."""
    global _http_client
    if _http_client is not None:
        _http_client.close()
        _http_client = None
