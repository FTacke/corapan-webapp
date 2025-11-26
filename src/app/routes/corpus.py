"""Corpus routes and search endpoints.

NOTE: This module contains legacy routes that redirect to the new BlackLab-based
advanced search. The routes are kept for backward compatibility only.
"""

from __future__ import annotations

from flask import (
    Blueprint,
    Response,
    render_template,
    request,
    redirect,
    url_for,
)

blueprint = Blueprint("corpus", __name__, url_prefix="/corpus")


@blueprint.get("/")
def corpus_home() -> Response:
    """Corpus-Startseite - redirects to advanced search.

    PUBLIC ROUTE: No authentication required.
    """
    return redirect(url_for("advanced_search.index"))


@blueprint.get("/guia")
def guia() -> Response:
    """Guía para consultar el corpus (página estática, en español).

    Sólo renderiza el template y permite marcar el endpoint activo para el menú.
    """
    return render_template("pages/corpus_guia.html")


@blueprint.route("/search", methods=["GET", "POST"])
def search() -> Response:
    """Deprecated search endpoint - redirects to advanced search.

    NOTE: Simple search (SQL-based) has been removed.
    Token search now uses BlackLab via /search/advanced/token/search API endpoint.
    Advanced search uses /search/advanced UI with BlackLab.

    This route is kept only for backward compatibility and redirects to advanced search.
    """
    params = request.args.to_dict(flat=False)
    query_str = (
        ""
        if not params
        else ("?" + "&".join([f"{k}={v[0]}" for k, v in params.items()]))
    )
    return redirect(url_for("advanced_search.index") + query_str)


@blueprint.get("/search/datatables")
def search_datatables() -> Response:
    """Deprecated DataTables endpoint - redirects to advanced API.

    NOTE: This endpoint is deprecated.
    - Advanced search uses /search/advanced/data API endpoint (BlackLab)
    - Token search uses /search/advanced/token/search API endpoint (BlackLab)
    """
    return redirect(url_for("advanced_api.data"))


@blueprint.get("/tokens")
def token_lookup() -> Response:
    """Lookup Tokens by IDs - redirects to advanced token search endpoint.

    PUBLIC ROUTE: No authentication required.
    NOTE: Legacy route - token lookup now uses BlackLab via advanced API.
    """
    return redirect(url_for("advanced_api.token_search"))
