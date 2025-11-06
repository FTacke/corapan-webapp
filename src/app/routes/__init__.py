"""Blueprint registration."""
from __future__ import annotations

from flask import Flask

from . import admin, auth, corpus, media, public, atlas, player, editor, stats


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
]


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application."""
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
