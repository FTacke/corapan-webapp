"""Public routes."""
from __future__ import annotations

import logging
from flask import Blueprint, make_response, render_template, request, jsonify
from ..services.counters import counter_visits
from flask_jwt_extended import jwt_required
import httpx

logger = logging.getLogger(__name__)

blueprint = Blueprint("public", __name__)


@blueprint.before_app_request
def track_visits():
    if request.endpoint and not request.endpoint.startswith("static"):
        counter_visits.increment()


@blueprint.get("/")
def landing_page():
    """Render the landing page with embedded quick search."""
    return render_template("pages/index.html")


@blueprint.get("/health")
def health_check():
    """
    Health check endpoint for Docker/Kubernetes monitoring.
    
    Checks:
    - Flask app is running (HTTP 200)
    - BlackLab server is reachable (if BLS_BASE_URL is configured)
    
    Response:
    {
        "status": "healthy" | "degraded" | "unhealthy",
        "service": "corapan-web",
        "checks": {
            "flask": {"ok": true},
            "blacklab": {"ok": true|false, "url": "...", "error": "..."}
        }
    }
    """
    from ..extensions.http_client import BLS_BASE_URL, get_http_client
    
    checks = {
        "flask": {"ok": True}  # If we got here, Flask is healthy
    }
    
    # Check BlackLab availability (quick preflight)
    blacklab_check = {
        "url": BLS_BASE_URL,
        "ok": False,
        "error": None
    }
    
    try:
        client = get_http_client()
        # Try a simple status endpoint first, fall back to /
        response = client.get(f"{BLS_BASE_URL}/", timeout=3.0)  # Single timeout value for all operations
        if response.status_code in (200, 404):  # 200 = endpoint exists, 404 = BLS exists but endpoint doesn't
            blacklab_check["ok"] = True
            logger.debug(f"BlackLab health check OK at {BLS_BASE_URL}")
        else:
            blacklab_check["error"] = f"HTTP {response.status_code}"
            logger.warning(f"BlackLab health check returned {response.status_code}: {response.text[:100]}")
    except httpx.ConnectError:
        blacklab_check["error"] = "Connection refused / unreachable"
        logger.warning(f"BlackLab health check failed (ConnectError): {BLS_BASE_URL}")
    except httpx.TimeoutException:
        blacklab_check["error"] = "Timeout"
        logger.warning(f"BlackLab health check timed out: {BLS_BASE_URL}")
    except Exception as e:
        blacklab_check["error"] = f"{type(e).__name__}: {str(e)}"
        logger.warning(f"BlackLab health check error: {e}")
    
    checks["blacklab"] = blacklab_check
    
    # Determine overall status
    if checks["flask"]["ok"] and checks["blacklab"]["ok"]:
        overall_status = "healthy"
        http_code = 200
    elif checks["flask"]["ok"]:
        # Flask OK but BlackLab not available
        overall_status = "degraded"
        http_code = 200  # Still return 200 so Docker healthcheck passes for Flask
    else:
        overall_status = "unhealthy"
        http_code = 503
    
    return jsonify({
        "status": overall_status,
        "service": "corapan-web",
        "checks": checks
    }), http_code


@blueprint.get("/health/bls")
def health_check_bls():
    """
    Dedicated BlackLab health check for developer diagnostics.
    
    Response:
    {
        "ok": true|false,
        "url": "http://localhost:8081/blacklab-server",
        "status_code": 200 | error code,
        "error": "Connection refused" | null
    }
    """
    from ..extensions.http_client import BLS_BASE_URL, get_http_client
    
    logger.debug(f"BlackLab diagnostic check: {BLS_BASE_URL}")
    
    try:
        client = get_http_client()
        response = client.get(f"{BLS_BASE_URL}/", timeout=3.0)  # Single timeout value
        ok = response.status_code in (200, 404)
        
        return jsonify({
            "ok": ok,
            "url": BLS_BASE_URL,
            "status_code": response.status_code,
            "error": None
        }), 200 if ok else 502
        
    except httpx.ConnectError as e:
        logger.warning(f"BlackLab not reachable: {e}")
        return jsonify({
            "ok": False,
            "url": BLS_BASE_URL,
            "status_code": None,
            "error": f"Connection refused (check if BlackLab is running at {BLS_BASE_URL})"
        }), 502
        
    except httpx.TimeoutException:
        logger.warning(f"BlackLab timeout at {BLS_BASE_URL}")
        return jsonify({
            "ok": False,
            "url": BLS_BASE_URL,
            "status_code": None,
            "error": "Timeout (BlackLab not responding)"
        }), 504
        
    except Exception as e:
        logger.error(f"BlackLab health check error: {e}")
        return jsonify({
            "ok": False,
            "url": BLS_BASE_URL,
            "status_code": None,
            "error": f"{type(e).__name__}: {str(e)}"
        }), 500


@blueprint.get("/proyecto")
def proyecto_page():
    # Previously rendered the single proyecto page. Now show overview.
    return render_template("pages/proyecto_overview.html")


@blueprint.get("/proyecto/overview")
def proyecto_overview():
    # Named endpoint used by templates/nav: public.proyecto_overview
    return render_template("pages/proyecto_overview.html")


@blueprint.get("/proyecto/diseno")
def proyecto_diseno():
    return render_template("pages/proyecto_diseno.html")


@blueprint.get("/proyecto/estadisticas")
def proyecto_estadisticas():
    return render_template("pages/proyecto_estadisticas.html")


@blueprint.get("/proyecto/quienes-somos")
def proyecto_quienes_somos():
    return render_template("pages/proyecto_quienes_somos.html")

@blueprint.get("/proyecto/como-citar")
def proyecto_como_citar():
    return render_template("pages/proyecto_como_citar.html")


@blueprint.get("/atlas")
def atlas_page():
    """Atlas page - auth status affects UI (login buttons visibility)."""
    html = render_template("pages/atlas.html")
    
    # Prevent caching to ensure data-auth attribute is always current
    response = make_response(html)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Vary'] = 'Cookie'
    
    return response


@blueprint.get("/impressum")
def impressum_page():
    return render_template("pages/impressum.html")


@blueprint.get("/privacy")
def privacy_page():
    return render_template("pages/privacy.html")

@blueprint.get("/get_stats_all_from_db")
def get_stats_all_from_db():
    from ..services.atlas import fetch_overview
    response = jsonify(fetch_overview())
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response


@blueprint.get("/get_stats_files_from_db")
@jwt_required()
def get_stats_files_from_db():
    from ..services.atlas import fetch_file_metadata
    response = jsonify({"metadata_list": fetch_file_metadata()})
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Vary'] = 'Cookie'
    return response
