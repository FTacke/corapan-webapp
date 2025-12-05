"""Analytics API endpoints for anonymous usage tracking.

VARIANTE 3a: Nur aggregierte Zähler, KEINE Suchinhalte!

PRIVACY: No personal data is collected or stored.
- No IP addresses
- No user IDs
- No cookies
- No fingerprints
- No search query contents (nur Zähler!)

All data is aggregated and anonymous.

SECURITY:
- Event endpoint is CSRF-exempt (no @jwt_required, public sendBeacon)
- Origin validation prevents abuse from external sites
- All errors are logged but return 204 to avoid UX impact
"""

from __future__ import annotations

import logging
from datetime import date

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import text

from ..auth import Role
from ..auth.decorators import require_role
from ..extensions.sqlalchemy_ext import get_session

logger = logging.getLogger(__name__)

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

# Valid event types
VALID_EVENT_TYPES = {"visit", "search", "audio_play", "error"}

# Allowed origins for event tracking (abuse protection)
# In production, only requests from these origins will be counted
ALLOWED_ORIGINS = {
    # Local development
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # Production
    "https://corapan.online.uni-marburg.de",
    "http://corapan.online.uni-marburg.de",
}


def _is_origin_allowed() -> bool:
    """Check if request origin is allowed for tracking.

    Returns True if:
    - Origin header is in ALLOWED_ORIGINS
    - Origin is missing (same-origin request, no CORS)
    - Running in development/testing mode
    """
    origin = request.headers.get("Origin")

    # No Origin header = same-origin request (browser doesn't send it)
    if not origin:
        return True

    # Check against allowed list
    if origin in ALLOWED_ORIGINS:
        return True

    # In development/testing, allow all origins
    if current_app.debug or current_app.testing:
        return True

    # Check for custom allowed origins from config
    custom_origins = current_app.config.get("ANALYTICS_ALLOWED_ORIGINS", set())
    if origin in custom_origins:
        return True

    logger.warning(f"Analytics: Rejected event from unauthorized origin: {origin}")
    return False


@bp.post("/event")
def track_event():
    """Track an analytics event.

    PUBLIC ENDPOINT - No authentication required.
    CSRF-EXEMPT - No @jwt_required decorator (sendBeacon compatibility).

    Request body:
    {
        "type": "visit" | "search" | "audio_play" | "error",
        "payload": {
            "device": "mobile" | "desktop"  // for visit
        }
    }

    HINWEIS (Variante 3a):
    - payload.query wird IGNORIERT (keine Suchinhalte speichern!)
    - Nur der Zähler searches wird erhöht

    ABUSE PROTECTION:
    - Only requests from allowed origins are counted
    - Unknown origins receive 204 but no DB write

    Returns:
        204 No Content on success (or ignored)
        400 Bad Request if event type invalid

    NOTE: Errors are logged but never returned to client to avoid UX impact.
    """
    try:
        # ABUSE PROTECTION: Check origin before processing
        if not _is_origin_allowed():
            # Return 204 (success) but don't count - attacker doesn't know
            return "", 204

        data = request.get_json(silent=True) or {}
        event_type = data.get("type", "").lower()
        payload = data.get("payload", {})

        if event_type not in VALID_EVENT_TYPES:
            return "", 400

        today = date.today()

        with get_session() as session:
            if event_type == "visit":
                _track_visit(session, today, payload)
            elif event_type == "search":
                _track_search(session, today)  # payload ignoriert (Variante 3a)
            elif event_type == "audio_play":
                _track_audio_play(session, today)
            elif event_type == "error":
                _track_error(session, today)

        return "", 204

    except Exception as e:
        # Log but never fail - analytics must not impact UX
        logger.warning(f"Analytics event tracking failed: {e}")
        return "", 204


def _track_visit(session, today: date, payload: dict) -> None:
    """Increment visitor counter and device type."""
    device = payload.get("device", "desktop")
    is_mobile = device == "mobile"

    # Upsert pattern for Postgres
    stmt = text("""
        INSERT INTO analytics_daily (date, visitors, mobile, desktop)
        VALUES (:date, 1, :mobile, :desktop)
        ON CONFLICT (date) DO UPDATE SET
            visitors = analytics_daily.visitors + 1,
            mobile = analytics_daily.mobile + :mobile,
            desktop = analytics_daily.desktop + :desktop,
            updated_at = now()
    """)
    session.execute(
        stmt,
        {
            "date": today,
            "mobile": 1 if is_mobile else 0,
            "desktop": 0 if is_mobile else 1,
        },
    )


def _track_search(session, today: date) -> None:
    """Increment search counter.

    VARIANTE 3a: Nur Zähler erhöhen, KEINE Query-Inhalte speichern!
    payload wird ignoriert.
    """
    stmt = text("""
        INSERT INTO analytics_daily (date, searches)
        VALUES (:date, 1)
        ON CONFLICT (date) DO UPDATE SET
            searches = analytics_daily.searches + 1,
            updated_at = now()
    """)
    session.execute(stmt, {"date": today})


def _track_audio_play(session, today: date) -> None:
    """Increment audio play counter."""
    stmt = text("""
        INSERT INTO analytics_daily (date, audio_plays)
        VALUES (:date, 1)
        ON CONFLICT (date) DO UPDATE SET
            audio_plays = analytics_daily.audio_plays + 1,
            updated_at = now()
    """)
    session.execute(stmt, {"date": today})


def _track_error(session, today: date) -> None:
    """Increment error counter."""
    stmt = text("""
        INSERT INTO analytics_daily (date, errors)
        VALUES (:date, 1)
        ON CONFLICT (date) DO UPDATE SET
            errors = analytics_daily.errors + 1,
            updated_at = now()
    """)
    session.execute(stmt, {"date": today})


@bp.get("/stats")
@jwt_required()
@require_role(Role.ADMIN)
def get_stats():
    """Get aggregated analytics stats for admin dashboard.

    ADMIN ONLY - Requires JWT authentication.

    Query params:
        days: int (default 30) - Number of days to fetch (including today)

    Returns:
        {
            "daily": [...],      // Last N days of metrics (chronological)
            "totals_window": {...},  // Aggregierte Summen (Zeitfenster)
            "totals_overall": {...}  // Aggregierte Summen (gesamt)
            "period_days": int   // Actual days in window
        }

    HINWEIS (Variante 3a): Kein top_queries Feld! Keine Suchinhalte.

    NOTE: Off-by-one fix: days=30 means today + 29 days back = 30 days total
    """
    days = request.args.get("days", 30, type=int)
    days = min(max(days, 1), 365)  # Clamp to 1-365

    try:
        with get_session() as session:
            # Get daily metrics (days-1 to include today correctly)
            # Example: days=30 → CURRENT_DATE - 29 = today and 29 previous days = 30 total
            daily_stmt = text("""
                SELECT date, visitors, mobile, desktop, searches, audio_plays, errors
                FROM analytics_daily
                WHERE date >= CURRENT_DATE - (:days - 1)
                ORDER BY date DESC
            """)
            daily_result = session.execute(daily_stmt, {"days": days})
            daily = [
                {
                    "date": str(row.date),
                    "visitors": row.visitors,
                    "mobile": row.mobile,
                    "desktop": row.desktop,
                    "searches": row.searches,
                    "audio_plays": row.audio_plays,
                    "errors": row.errors,
                }
                for row in daily_result
            ]

            # Get totals for window (last N days, including today)
            totals_stmt = text("""
                SELECT 
                    COALESCE(SUM(visitors), 0) as visitors,
                    COALESCE(SUM(mobile), 0) as mobile,
                    COALESCE(SUM(desktop), 0) as desktop,
                    COALESCE(SUM(searches), 0) as searches,
                    COALESCE(SUM(audio_plays), 0) as audio_plays,
                    COALESCE(SUM(errors), 0) as errors
                FROM analytics_daily
                WHERE date >= CURRENT_DATE - (:days - 1)
            """)
            totals_row = session.execute(totals_stmt, {"days": days}).fetchone()
            totals_window = {
                "visitors": totals_row.visitors,
                "mobile": totals_row.mobile,
                "desktop": totals_row.desktop,
                "searches": totals_row.searches,
                "audio_plays": totals_row.audio_plays,
                "errors": totals_row.errors,
            }

            # Get overall totals (all time)
            overall_stmt = text("""
                SELECT 
                    COALESCE(SUM(visitors), 0) as visitors,
                    COALESCE(SUM(mobile), 0) as mobile,
                    COALESCE(SUM(desktop), 0) as desktop,
                    COALESCE(SUM(searches), 0) as searches,
                    COALESCE(SUM(audio_plays), 0) as audio_plays,
                    COALESCE(SUM(errors), 0) as errors
                FROM analytics_daily
            """)
            overall_row = session.execute(overall_stmt).fetchone()
            totals_overall = {
                "visitors": overall_row.visitors,
                "mobile": overall_row.mobile,
                "desktop": overall_row.desktop,
                "searches": overall_row.searches,
                "audio_plays": overall_row.audio_plays,
                "errors": overall_row.errors,
            }

            # HINWEIS: Keine top_queries Abfrage (Variante 3a)

            return jsonify(
                {
                    "daily": daily,
                    "totals_window": totals_window,
                    "totals_overall": totals_overall,
                    "period_days": days,
                }
            )
            # KEIN top_queries Feld!
    except Exception as e:
        # Log the error and return a helpful message
        error_msg = str(e)
        if "analytics_daily" in error_msg.lower() and (
            "does not exist" in error_msg.lower() or "undefined" in error_msg.lower()
        ):
            logger.error(f"Analytics table missing: {e}")
            return jsonify(
                {
                    "error": "Analytics table not found. Database migration 0002 may not have been applied.",
                    "detail": "Run: python scripts/setup_prod_db.py",
                }
            ), 500
        logger.error(f"Analytics stats query failed: {e}")
        return jsonify(
            {"error": "Failed to fetch analytics data", "detail": str(e)}
        ), 500
