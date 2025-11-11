"""Admin-only routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, render_template
from flask_jwt_extended import jwt_required

from ..auth import Role
from ..auth.decorators import require_role
from ..services.counters import counter_access, counter_search, counter_visits

blueprint = Blueprint("admin", __name__, url_prefix="/admin")


@blueprint.get("/dashboard")
@jwt_required()
@require_role(Role.ADMIN)
def dashboard():
    return render_template("pages/admin_dashboard.html")


@blueprint.get("/metrics")
@jwt_required()
@require_role(Role.ADMIN)
def metrics():
    payload = {
        "access": counter_access.load(),
        "visits": counter_visits.load(),
        "search": counter_search.load(),
    }
    return jsonify(payload)