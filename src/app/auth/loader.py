"""Hydrate credential store from environment variables."""

from __future__ import annotations

import os

from . import Role
from ..routes import auth


def _parse_role_account(env_key: str) -> tuple[Role, str]:
    token = env_key.removesuffix("_PASSWORD_HASH")  # strip suffix
    if "__" in token:
        role_token, account_token = token.split("__", 1)
    else:
        role_token, account_token = token, token
    role_value = role_token.lower()
    account = account_token.lower()
    try:
        role = Role(role_value)
    except ValueError:
        role = Role.USER
    return role, account


def hydrate() -> None:
    """Populate the credential map based on *_PASSWORD_HASH environment values.

    This function will only load credentials when the AUTH_BACKEND is configured
    to 'env'. In staging/production (AUTH_BACKEND=db) the legacy env-based
    credential loader is skipped to avoid creating a parallel auth path.
    """
    auth.CREDENTIALS.clear()
    backend = os.getenv("AUTH_BACKEND", "env").lower()
    if backend != "env":
        # intentionally skip hydrating credentials when DB-backed auth is active
        # to avoid accidental dual-auth behaviour in non-dev environments.
        # In dev environments it's still convenient to use passwords.env.
        try:
            import logging

            logging.getLogger(__name__).info(
                "Skipping env-based credential hydration because AUTH_BACKEND=%s", backend
            )
        except Exception:
            pass
        return

    for key, value in os.environ.items():
        if not key.endswith("_PASSWORD_HASH"):
            continue
        role, account = _parse_role_account(key)
        auth.CREDENTIALS[account] = auth.Credential(role=role, password_hash=value)
