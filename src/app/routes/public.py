"""Public routes."""
from __future__ import annotations

from flask import Blueprint, make_response, render_template, request, jsonify
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
