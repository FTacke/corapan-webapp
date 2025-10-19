"""Public routes."""
from __future__ import annotations

from flask import Blueprint, render_template, request, jsonify, abort, g

from ..services.counters import counter_visits
from flask_jwt_extended import jwt_required

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
    """Health check endpoint for Docker/Kubernetes monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "corapan-web"
    }), 200


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


@blueprint.get("/proyecto/referencias")
def proyecto_referencias():
    return render_template("pages/proyecto_referencias.html")


@blueprint.get("/proyecto/como-citar")
def proyecto_como_citar():
    return render_template("pages/proyecto_como_citar.html")


@blueprint.get("/atlas")
def atlas_page():
    return render_template("pages/atlas.html")


@blueprint.get("/impressum")
def impressum_page():
    return render_template("pages/impressum.html")


@blueprint.get("/privacy")
def privacy_page():
    return render_template("pages/privacy.html")

@blueprint.get("/get_stats_all_from_db")
def get_stats_all_from_db():
    from ..services.atlas import fetch_overview
    return jsonify(fetch_overview())


@blueprint.get("/get_stats_files_from_db")
@jwt_required(optional=True)
def get_stats_files_from_db():
    from ..services.atlas import fetch_file_metadata
    if getattr(g, "user", None) is None:
        abort(401)
    return jsonify({"metadata_list": fetch_file_metadata()})
