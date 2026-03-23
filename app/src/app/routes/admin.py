"""Admin-only routes."""

from __future__ import annotations

from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required

from ..auth import Role
from ..auth.decorators import require_role

blueprint = Blueprint("admin", __name__, url_prefix="/admin")


@blueprint.get("/dashboard")
@jwt_required()
@require_role(Role.ADMIN)
def dashboard():
    return render_template("pages/admin_dashboard.html")


# NOTE: /metrics endpoint removed - replaced by /api/analytics/stats
# See src/app/routes/analytics.py for new anonymous analytics API
