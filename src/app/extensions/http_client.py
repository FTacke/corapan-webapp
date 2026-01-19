"""HTTP client for external API proxying (BlackLab, etc.).

Configuration:
    BLS_BASE_URL: Base URL for BlackLab Server (CQL/FCS interface)
        - Environment variable: BLS_BASE_URL
        - Default (development): http://localhost:8081/blacklab-server
        - Example (Docker): http://blacklab:8081/blacklab-server
        - Must include protocol and path, trailing slash will be removed

        Set before creating the app:
            export BLS_BASE_URL=http://localhost:8080/blacklab-server  # for dev

        Or in passwords.env (loaded at startup):
            BLS_BASE_URL=http://localhost:8081/blacklab-server
"""

from __future__ import annotations

import os
import time
import logging
import httpx
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Singleton HTTP client for persistent connections and connection pooling
_http_client: Optional[httpx.Client] = None

# Get BLS base URL from environment (required for proxying)
# Default: http://localhost:8081/blacklab-server (Docker on local port 8081)
# For dev without Docker: http://localhost:8080/blacklab-server (typical BLS port)
BLS_BASE_URL = os.environ.get(
    "BLS_BASE_URL", "http://localhost:8081/blacklab-server"
).rstrip("/")

# Configurable BlackLab corpus name (default matches production)
BLS_CORPUS = (os.environ.get("BLS_CORPUS", "index") or "index").strip() or "index"

# Corpus availability cache
_CORPORA_CACHE_TTL = 60.0
_CORPORA_CACHE: Dict[str, object] = {"ts": 0.0, "corpora": None}
_CORPUS_CHECKED = False


class BlackLabCorpusNotFound(RuntimeError):
    """Raised when configured BLS_CORPUS is not present on the BlackLab server."""


def build_bls_corpus_path(endpoint: Optional[str] = None) -> str:
    """Build a BlackLab v5 corpus path for the configured corpus."""
    if endpoint:
        endpoint = endpoint.lstrip("/")
        return f"/corpora/{BLS_CORPUS}/{endpoint}"
    return f"/corpora/{BLS_CORPUS}"


def _parse_corpora_payload(payload: object) -> list[str]:
    """Parse a BlackLab /corpora JSON payload into a list of corpus IDs."""
    if not isinstance(payload, dict):
        return []

    corpora = payload.get("corpora") or payload.get("corpus") or payload.get("list")
    if isinstance(corpora, dict):
        return [str(key) for key in corpora.keys()]
    if isinstance(corpora, list):
        results = []
        for item in corpora:
            if isinstance(item, str):
                results.append(item)
            elif isinstance(item, dict):
                corpus_id = item.get("corpusId") or item.get("id") or item.get("name")
                if corpus_id:
                    results.append(str(corpus_id))
        return results
    return []


def get_available_corpora(force: bool = False) -> list[str]:
    """Fetch available corpora from BlackLab (cached for a short TTL)."""
    global _CORPORA_CACHE

    now = time.time()
    cached = _CORPORA_CACHE.get("corpora")
    if not force and cached is not None:
        age = now - float(_CORPORA_CACHE.get("ts", 0.0))
        if age < _CORPORA_CACHE_TTL:
            return list(cached)

    try:
        client = get_http_client()
        response = client.get(
            f"{BLS_BASE_URL}/corpora",
            params={"outputformat": "json"},
            headers={"Accept": "application/json"},
            timeout=httpx.Timeout(3.0, read=3.0, write=3.0, pool=3.0),
        )
        response.raise_for_status()
        corpora = _parse_corpora_payload(response.json())
        _CORPORA_CACHE = {"ts": now, "corpora": corpora}
        return list(corpora)
    except Exception as exc:
        logger.debug(f"Failed to fetch BlackLab corpora list: {exc}")
        return []


def format_corpus_not_found_message(corpus: str, available: list[str]) -> str:
    """Build a clear message when the configured corpus is missing."""
    available_str = ", ".join(available) if available else "<none>"
    return f"Configured BLS_CORPUS='{corpus}' not found. Available: {available_str}."


def get_corpus_not_found_message(response: httpx.Response) -> str | None:
    """Return a friendly message if the response indicates a missing corpus."""
    text = response.text or ""
    if response.status_code == 404 or "CANNOT_OPEN_INDEX" in text:
        available = get_available_corpora(force=True)
        return format_corpus_not_found_message(BLS_CORPUS, available)
    return None


def warn_if_configured_corpus_missing() -> None:
    """Warn once if configured corpus is not present on the server."""
    global _CORPUS_CHECKED
    if _CORPUS_CHECKED:
        return
    _CORPUS_CHECKED = True

    available = get_available_corpora()
    if available and BLS_CORPUS not in available:
        logger.warning(format_corpus_not_found_message(BLS_CORPUS, available))


def get_http_client() -> httpx.Client:
    """Get or create singleton httpx.Client with connection pooling to BLS.

    Uses BLS_BASE_URL from environment (default: http://localhost:8081/blacklab-server).
    All requests should pass the full path (e.g., "/corapan/hits").
    """
    global _http_client

    if _http_client is None:
        _http_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=5.0,  # Connection timeout (shorter for proxy)
                read=30.0,  # Read timeout (reasonable for search)
                write=5.0,  # Write timeout
                pool=5.0,  # Pool timeout (required in httpx 0.27+)
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
