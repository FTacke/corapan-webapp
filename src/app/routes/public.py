"""Public routes."""

from __future__ import annotations

import logging
from flask import (
    Blueprint,
    make_response,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
)
from flask_jwt_extended import jwt_required
import httpx

logger = logging.getLogger(__name__)

blueprint = Blueprint("public", __name__)

# NOTE: Visit tracking moved to new analytics system (see src/app/routes/analytics.py)
# Frontend now calls /api/analytics/event directly via static/js/modules/analytics.js


@blueprint.get("/")
def landing_page():
    """Render the landing page with embedded quick search."""
    return render_template("pages/index.html", page_name="index")


@blueprint.get("/login", endpoint="login")
def login_page():
    """Render a full-page login screen.

    This is the canonical login page for the site (public /login). It
    renders the existing template `templates/auth/login.html` and accepts
    an optional `next` query parameter for redirect-after-login.
    """
    next_url = request.args.get("next") or ""

    # Render the full login page (no caching)
    response = make_response(render_template("auth/login.html", next=next_url))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Vary"] = "Cookie"
    return response, 200


@blueprint.get("/health")
def health_check():
    """
    Health check endpoint for Docker/Kubernetes monitoring.

    Checks:
    - Flask app is running (HTTP 200)
    - Auth database is reachable (SELECT 1)
    - BlackLab server is reachable (if BLS_BASE_URL is configured)

    Response:
    {
        "status": "healthy" | "degraded" | "unhealthy",
        "service": "corapan-web",
        "checks": {
            "flask": {"ok": true},
            "auth_db": {"ok": true|false, "backend": "postgresql|sqlite", "error": "..."},
            "blacklab": {"ok": true|false, "url": "...", "error": "..."}
        }
    }

    HTTP Status:
    - 200: All critical checks pass (auth_db OK)
    - 503: Critical checks fail (auth_db down)
    """
    from ..extensions.http_client import BLS_BASE_URL, get_http_client
    from ..extensions.sqlalchemy_ext import get_engine
    from sqlalchemy import text

    checks = {
        "flask": {"ok": True}  # If we got here, Flask is healthy
    }

    # Check Auth DB availability (critical for production)
    auth_db_check = {"ok": False, "backend": None, "error": None}
    try:
        engine = get_engine()
        if engine is None:
            auth_db_check["error"] = "Auth engine not initialized"
        else:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            auth_db_check["ok"] = True
            # Determine backend type
            url = str(engine.url)
            if "sqlite" in url:
                auth_db_check["backend"] = "sqlite"
            elif "postgresql" in url or "postgres" in url:
                auth_db_check["backend"] = "postgresql"
            else:
                auth_db_check["backend"] = "unknown"
    except Exception as e:
        auth_db_check["error"] = f"{type(e).__name__}: {str(e)}"
        logger.warning(f"Auth DB health check failed: {e}")

    checks["auth_db"] = auth_db_check

    # Check BlackLab availability (quick preflight)
    blacklab_check = {"url": BLS_BASE_URL, "ok": False, "error": None}

    try:
        client = get_http_client()
        # Try a simple status endpoint first, fall back to /
        response = client.get(
            f"{BLS_BASE_URL}/", timeout=3.0
        )  # Single timeout value for all operations
        if response.status_code in (
            200,
            404,
        ):  # 200 = endpoint exists, 404 = BLS exists but endpoint doesn't
            blacklab_check["ok"] = True
            logger.debug(f"BlackLab health check OK at {BLS_BASE_URL}")
        else:
            blacklab_check["error"] = f"HTTP {response.status_code}"
            logger.warning(
                f"BlackLab health check returned {response.status_code}: {response.text[:100]}"
            )
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
    # Auth DB is critical, BlackLab is not (degraded mode still works)
    if checks["flask"]["ok"] and checks["auth_db"]["ok"] and checks["blacklab"]["ok"]:
        overall_status = "healthy"
        http_code = 200
    elif checks["flask"]["ok"] and checks["auth_db"]["ok"]:
        # Flask + Auth OK but BlackLab not available - degraded but functional
        overall_status = "degraded"
        http_code = 200
    elif checks["flask"]["ok"] and not checks["auth_db"]["ok"]:
        # Auth DB down - critical failure
        overall_status = "unhealthy"
        http_code = 503
    else:
        overall_status = "unhealthy"
        http_code = 503

    return jsonify(
        {"status": overall_status, "service": "corapan-web", "checks": checks}
    ), http_code


@blueprint.get("/health/bls")
def health_check_bls():
    """
    Dedicated BlackLab health check for developer diagnostics.

    Returns the configured BLS_BASE_URL and connection status.
    In local dev, this normally shows http://localhost:8081/blacklab-server
    (Docker-BlackLab on port 8081, matching the default BLS_BASE_URL).

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

        return jsonify(
            {
                "ok": ok,
                "url": BLS_BASE_URL,
                "status_code": response.status_code,
                "error": None,
            }
        ), 200 if ok else 502

    except httpx.ConnectError as e:
        logger.warning(f"BlackLab not reachable: {e}")
        return jsonify(
            {
                "ok": False,
                "url": BLS_BASE_URL,
                "status_code": None,
                "error": f"Connection refused (check if BlackLab is running at {BLS_BASE_URL})",
            }
        ), 502

    except httpx.TimeoutException:
        logger.warning(f"BlackLab timeout at {BLS_BASE_URL}")
        return jsonify(
            {
                "ok": False,
                "url": BLS_BASE_URL,
                "status_code": None,
                "error": "Timeout (BlackLab not responding)",
            }
        ), 504

    except Exception as e:
        logger.error(f"BlackLab health check error: {e}")
        return jsonify(
            {
                "ok": False,
                "url": BLS_BASE_URL,
                "status_code": None,
                "error": f"{type(e).__name__}: {str(e)}",
            }
        ), 500


@blueprint.get("/health/auth")
def health_check_auth():
    """
    Dedicated Auth DB health check for developer diagnostics.

    Returns the auth database connection status.
    Useful for verifying the auth backend is operational.

    Response:
    {
        "ok": true|false,
        "backend": "sqlite" | "postgresql",
        "error": null | "Connection failed"
    }
    """
    from ..extensions.sqlalchemy_ext import get_engine
    from sqlalchemy import text

    try:
        engine = get_engine()
        if engine is None:
            return jsonify(
                {
                    "ok": False,
                    "backend": None,
                    "error": "Auth engine not initialized (AUTH_DATABASE_URL may be unset)",
                }
            ), 503

        # Try a simple query to verify connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Determine backend type from URL
        url = str(engine.url)
        if "sqlite" in url:
            backend = "sqlite"
        elif "postgresql" in url or "postgres" in url:
            backend = "postgresql"
        else:
            backend = "unknown"

        return jsonify({"ok": True, "backend": backend, "error": None}), 200

    except Exception as e:
        logger.error(f"Auth DB health check error: {e}")
        return jsonify(
            {"ok": False, "backend": None, "error": f"{type(e).__name__}: {str(e)}"}
        ), 503


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
    # Redirect to corpus metadata page (composicion merged into metadata)
    return redirect(url_for("corpus.metadata"), 301)


@blueprint.get("/proyecto/quienes-somos")
def proyecto_quienes_somos():
    return render_template("pages/proyecto_quienes_somos.html")


@blueprint.get("/proyecto/como-citar")
def proyecto_como_citar():
    return render_template("pages/proyecto_como_citar.html")


@blueprint.get("/proyecto/referencias")
def proyecto_referencias():
    return render_template("pages/proyecto_referencias.html")


@blueprint.get("/atlas")
def atlas_page():
    """Atlas page - auth status affects UI (login buttons visibility)."""
    html = render_template("pages/atlas.html")

    # Prevent caching to ensure data-auth attribute is always current
    response = make_response(html)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Vary"] = "Cookie"

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
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response


@blueprint.get("/get_stats_files_from_db")
@jwt_required()
def get_stats_files_from_db():
    from ..services.atlas import fetch_file_metadata

    response = jsonify({"metadata_list": fetch_file_metadata()})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Vary"] = "Cookie"
    return response
