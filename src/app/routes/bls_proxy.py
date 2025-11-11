"""BlackLab Server proxy via /bls/** routes."""
from __future__ import annotations

import logging
from urllib.parse import urljoin

from flask import Blueprint, request, Response
from ..extensions.http_client import get_http_client

logger = logging.getLogger(__name__)

# Blueprint setup
bp = Blueprint("bls", __name__, url_prefix="/bls")

# BlackLab Server upstream
BLS_UPSTREAM = "http://127.0.0.1:8081/blacklab-server"

# Hop-by-hop headers to remove (per RFC 7230)
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
}


def _remove_hop_by_hop_headers(headers: dict) -> dict:
    """Remove hop-by-hop headers from response."""
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}


def _build_upstream_url(path: str) -> str:
    """Build upstream URL from path."""
    # Ensure path starts with /
    if not path:
        path = "/"
    elif not path.startswith("/"):
        path = "/" + path

    # Remove any double slashes
    while "//" in path:
        path = path.replace("//", "/")

    return urljoin(BLS_UPSTREAM, path.lstrip("/"))


def _proxy_request(method: str, path: str) -> Response:
    """Proxy HTTP request to BlackLab Server."""
    upstream_url = _build_upstream_url(path)

    logger.debug(f"Proxying {method} {path} → {upstream_url}")

    try:
        client = get_http_client()

        # Forward request headers (exclude host/connection headers)
        headers = {
            k: v
            for k, v in request.headers
            if k.lower() not in {"host", "connection", "transfer-encoding", "content-length"}
        }

        # Make upstream request
        upstream_response = client.request(
            method=method,
            url=upstream_url,
            headers=headers,
            params=request.args.to_dict(flat=False) if request.args else None,
            content=request.get_data(),
            follow_redirects=False,
        )

        # Remove hop-by-hop headers from response
        response_headers = _remove_hop_by_hop_headers(dict(upstream_response.headers))

        # Stream response back to client
        def generate():
            for chunk in upstream_response.iter_raw(chunk_size=65536):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            status=upstream_response.status_code,
            headers=response_headers,
            mimetype=upstream_response.headers.get("content-type", "application/json"),
        )

    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return Response(
            f'{{"error": "proxy_error", "message": "{str(e)}"}}',
            status=502,
            mimetype="application/json",
        )


@bp.route("/", methods=["GET"])
@bp.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy(path: str = ""):
    """Proxy all requests to BlackLab Server."""
    return _proxy_request(request.method, path)


@bp.errorhandler(404)
def handle_404(e):
    """Handle 404 in proxy."""
    logger.debug(f"BLS proxy 404: {request.path}")
    return (
        '{"error": "not_found", "message": "BlackLab resource not found"}',
        404,
        {"Content-Type": "application/json"},
    )
