"""Entry point for running the application via python -m src.app.main."""
from __future__ import annotations

import os

from . import create_app


def _resolve_env() -> str:
    env_name = os.getenv("FLASK_ENV")
    if env_name:
        return env_name
    env_name = "development"
    os.environ["FLASK_ENV"] = env_name
    return env_name


app = create_app(_resolve_env())


if __name__ == "__main__":
    debug_mode = _resolve_env() == "development"
    app.run(host="0.0.0.0", port=8000, debug=debug_mode)
