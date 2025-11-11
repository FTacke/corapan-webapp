"""Blueprint registration."""
from __future__ import annotations

from flask import Flask

from . import admin, auth, corpus, media, public, atlas, player, editor, stats, bls_proxy
from ..search import advanced, advanced_api


BLUEPRINTS = [
    public.blueprint,
    auth.blueprint,
    corpus.blueprint,
    media.blueprint,
    admin.blueprint,
    atlas.blueprint,  # New versioned API: /api/v1/atlas/*
    atlas.legacy_blueprint,  # Legacy redirects: /atlas/* -> /api/v1/atlas/*
    player.blueprint,
    editor.blueprint,  # Editor for Admin/Editor roles
    stats.blueprint,  # Stats API: /api/stats (public read-only)
    bls_proxy.bp,  # BlackLab Server proxy: /bls/**
    advanced.bp,  # Advanced search UI: /search/advanced
    advanced_api.bp,  # Advanced search API: /search/advanced/data, /search/advanced/export
]


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application."""
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
