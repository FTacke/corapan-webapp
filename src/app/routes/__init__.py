"""Blueprint registration."""
from __future__ import annotations

from flask import Flask

from . import admin, auth, corpus, media, public, atlas, player


BLUEPRINTS = [
    public.blueprint,
    auth.blueprint,
    corpus.blueprint,
    media.blueprint,
    admin.blueprint,
    atlas.blueprint,  # New versioned API: /api/v1/atlas/*
    atlas.legacy_blueprint,  # Legacy redirects: /atlas/* -> /api/v1/atlas/*
    player.blueprint,
]


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask application."""
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
