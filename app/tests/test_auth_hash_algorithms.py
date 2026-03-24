import os
from pathlib import Path

import pytest
from flask import Flask

os.environ.setdefault("CORAPAN_RUNTIME_ROOT", str(Path(__file__).resolve().parents[2]))
os.environ.setdefault(
    "CORAPAN_MEDIA_ROOT", str(Path(__file__).resolve().parents[2] / "media")
)
os.environ.setdefault("BLS_CORPUS", "corapan")

from src.app.auth import services


def _make_app(algo: str) -> Flask:
    app = Flask(__name__)
    app.config["AUTH_HASH_ALGO"] = algo
    app.config["AUTH_ARGON2_TIME_COST"] = 2
    app.config["AUTH_ARGON2_MEMORY_COST"] = 102400
    app.config["AUTH_ARGON2_PARALLELISM"] = 4
    return app


@pytest.mark.parametrize("algo", ["argon2", "bcrypt"])
def test_hash_password_round_trip_for_supported_algorithms(algo: str):
    app = _make_app(algo)
    with app.app_context():
        hashed = services.hash_password("StrongPass123")
        assert services.verify_password("StrongPass123", hashed)


def test_verify_password_accepts_legacy_bcrypt_hash_when_current_algo_is_argon2():
    bcrypt_app = _make_app("bcrypt")
    with bcrypt_app.app_context():
        legacy_hash = services.hash_password("LegacyPass123")

    argon2_app = _make_app("argon2")
    with argon2_app.app_context():
        assert services.verify_password("LegacyPass123", legacy_hash)


def test_verify_password_accepts_argon2_hash_when_current_algo_is_bcrypt():
    argon2_app = _make_app("argon2")
    with argon2_app.app_context():
        modern_hash = services.hash_password("ModernPass123")

    bcrypt_app = _make_app("bcrypt")
    with bcrypt_app.app_context():
        assert services.verify_password("ModernPass123", modern_hash)