"""Blueprint registration."""

from __future__ import annotations

from flask import Flask

from . import admin, auth, media, public, atlas, player, editor, stats, bls_proxy, corpus, admin_users, analytics
from ..search import advanced, advanced_api


BLUEPRINTS = [
    public.blueprint,
    auth.blueprint,
    media.blueprint,
    admin.blueprint,
    atlas.blueprint,  # New versioned API: /api/v1/atlas/*
    atlas.legacy_blueprint,  # Legacy redirects: /atlas/* -> /api/v1/atlas/*
    player.blueprint,
    editor.blueprint,  # Editor for Admin/Editor roles
    stats.blueprint,  # Stats API: /api/stats (public read-only)
    bls_proxy.bp,  # BlackLab Server proxy: /bls/**
    advanced.bp,  # Advanced search UI: /search/advanced
    corpus.blueprint,  # Corpus informational routes (e.g. /corpus/guia)
    advanced_api.bp,  # Advanced search API: /search/advanced/data, /search/advanced/export
    admin_users.bp,
    analytics.bp,  # Analytics API: /api/analytics/* (VARIANTE 3a: nur Zähler)
]


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application."""
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
