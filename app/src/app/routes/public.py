"""Public routes."""

from __future__ import annotations

import re
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from flask import (
    Blueprint,
    current_app,
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

_SECRET_URL_RE = re.compile(
    r"(?P<scheme>[a-zA-Z][a-zA-Z0-9+.-]*://)(?P<user>[^:/?#@\s]+)(?::(?P<password>[^@\s/?#]*))?@"
)
_PASSWORD_PAIR_RE = re.compile(r"(?i)(password|passwd|pwd)=([^\s&]+)")
_URI_RE = re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s'\"]+")


def _redact_sensitive_text(value: str | None) -> str:
    if not value:
        return ""

    redacted = str(value)
    redacted = _SECRET_URL_RE.sub(r"\g<scheme>\g<user>:***@", redacted)
    redacted = _PASSWORD_PAIR_RE.sub(r"\1=***", redacted)
    redacted = _URI_RE.sub("<redacted-url>", redacted)
    return redacted


def _exception_summary(exc: Exception) -> tuple[str, str]:
    exc_type = type(exc).__name__
    message = _redact_sensitive_text(str(exc)).strip()
    return exc_type, message


def _engine_backend_name(engine) -> str:
    dialect = getattr(engine, "dialect", None)
    return getattr(dialect, "name", "unknown") or "unknown"


def _run_timed_check(
    name: str,
    check_fn,
    *,
    timeout_s: float,
    failure_status: str,
) -> dict[str, object]:
    start = time.perf_counter()
    result: dict[str, object] = {"ok": True, "status": "healthy"}
    executor = ThreadPoolExecutor(max_workers=1)

    try:
        future = executor.submit(check_fn)
        payload = future.result(timeout=timeout_s)
        if isinstance(payload, dict):
            result.update(payload)
    except FutureTimeout:
        result.update(
            {
                "ok": False,
                "status": failure_status,
                "error": "TimeoutError",
                "message": f"timed out after {timeout_s:.2f}s",
                "timeout_s": timeout_s,
            }
        )
    except Exception as exc:
        exc_type, message = _exception_summary(exc)
        result.update(
            {
                "ok": False,
                "status": failure_status,
                "error": exc_type,
                "message": message or None,
            }
        )
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    result["ms"] = elapsed_ms

    if not result.get("ok", False):
        error_type = str(result.get("error") or "error")
        message = str(result.get("message") or "")
        log_fn = logger.error if failure_status == "unhealthy" else logger.warning
        if message:
            log_fn(
                "Readiness subcheck failed: check=%s status=%s duration_ms=%s timeout_s=%.2f error=%s: %s",
                name,
                result.get("status"),
                elapsed_ms,
                timeout_s,
                error_type,
                message,
            )
        else:
            log_fn(
                "Readiness subcheck failed: check=%s status=%s duration_ms=%s timeout_s=%.2f error=%s",
                name,
                result.get("status"),
                elapsed_ms,
                timeout_s,
                error_type,
            )

    return result

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
    """Liveness check for Docker/Kubernetes monitoring."""

    return jsonify(
        {
            "status": "healthy",
            "service": "corapan",
            "checks": {"flask": True},
        }
    ), 200


@blueprint.get("/ready")
def readiness_check():
    """Readiness check for auth DB and BlackLab dependencies."""

    from sqlalchemy import text

    from ..extensions.http_client import get_http_client
    from ..extensions.sqlalchemy_ext import get_engine

    bls_base_url = (current_app.config.get("BLS_BASE_URL") or "").rstrip("/")
    bls_corpus = (current_app.config.get("BLS_CORPUS") or "").strip()

    def check_auth_db() -> dict[str, object]:
        engine = get_engine()
        if engine is None:
            raise RuntimeError("Auth engine not initialized")

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {"backend": _engine_backend_name(engine)}

    def _extract_corpora_ids(payload: object) -> list[str]:
        if not isinstance(payload, dict):
            return []

        corpora = payload.get("corpora") or payload.get("corpus") or payload.get("list")
        if isinstance(corpora, dict):
            return [str(key) for key in corpora.keys()]
        if isinstance(corpora, list):
            values: list[str] = []
            for item in corpora:
                if isinstance(item, str):
                    values.append(item)
                elif isinstance(item, dict):
                    corpus_id = item.get("corpusId") or item.get("id") or item.get("name")
                    if corpus_id:
                        values.append(str(corpus_id))
            return values
        return []

    def check_blacklab() -> dict[str, object]:
        if not bls_base_url:
            raise RuntimeError("BLS_BASE_URL is not configured")

        client = get_http_client()
        response = client.get(
            f"{bls_base_url}/corpora",
            params={"outputformat": "json"},
            headers={"Accept": "application/json"},
            timeout=httpx.Timeout(0.8),
        )
        response.raise_for_status()

        available_corpora = _extract_corpora_ids(response.json())
        if available_corpora and bls_corpus and bls_corpus not in available_corpora:
            raise RuntimeError(
                f"Configured corpus '{bls_corpus}' is not available on BlackLab"
            )

        return {
            "url": bls_base_url,
            "corpus": bls_corpus,
            "available_corpora": len(available_corpora),
        }

    checks = {
        "flask": {"ok": True, "status": "healthy", "ms": 0},
        "auth_db": _run_timed_check(
            "auth_db",
            check_auth_db,
            timeout_s=0.8,
            failure_status="unhealthy",
        ),
        "blacklab": _run_timed_check(
            "blacklab",
            check_blacklab,
            timeout_s=0.8,
            failure_status="degraded",
        ),
    }

    if not checks["auth_db"]["ok"]:
        overall_status = "unhealthy"
        http_code = 503
    elif not checks["blacklab"]["ok"]:
        overall_status = "degraded"
        http_code = 200
    else:
        overall_status = "healthy"
        http_code = 200

    return jsonify(
        {"status": overall_status, "service": "corapan", "checks": checks}
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

    logger.debug("BlackLab diagnostic check: %s", BLS_BASE_URL)

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
        logger.warning("BlackLab not reachable: %s", _redact_sensitive_text(str(e)))
        return jsonify(
            {
                "ok": False,
                "url": BLS_BASE_URL,
                "status_code": None,
                "error": f"Connection refused (check if BlackLab is running at {BLS_BASE_URL})",
            }
        ), 502

    except httpx.TimeoutException:
        logger.warning("BlackLab timeout at %s", BLS_BASE_URL)
        return jsonify(
            {
                "ok": False,
                "url": BLS_BASE_URL,
                "status_code": None,
                "error": "Timeout (BlackLab not responding)",
            }
        ), 504

    except Exception as e:
        logger.error(
            "BlackLab health check error: %s", _redact_sensitive_text(str(e))
        )
        return jsonify(
            {
                "ok": False,
                "url": BLS_BASE_URL,
                "status_code": None,
                "error": _redact_sensitive_text(f"{type(e).__name__}: {str(e)}"),
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

        backend = _engine_backend_name(engine)

        return jsonify({"ok": True, "backend": backend, "error": None}), 200

    except Exception as e:
        logger.error("Auth DB health check error: %s", _redact_sensitive_text(str(e)))
        return jsonify(
            {
                "ok": False,
                "backend": None,
                "error": _redact_sensitive_text(f"{type(e).__name__}: {str(e)}"),
            }
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


@blueprint.get("/get_stats_files_from_db")
@jwt_required()
def get_stats_files_from_db():
    from ..services.atlas import fetch_file_metadata

    response = jsonify({"metadata_list": fetch_file_metadata()})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Vary"] = "Cookie"
    return response
