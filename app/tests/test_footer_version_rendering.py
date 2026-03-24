import os
from pathlib import Path

from flask import Flask, render_template

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("CORAPAN_RUNTIME_ROOT", str(WORKSPACE_ROOT))
os.environ.setdefault("CORAPAN_MEDIA_ROOT", str(WORKSPACE_ROOT / "media"))

from src.app import register_context_processors
from src.app.config import resolve_app_release_metadata


def make_app() -> Flask:
    project_root = Path(__file__).resolve().parents[1]
    template_dir = project_root / "templates"
    static_dir = project_root / "static"

    app = Flask(
        __name__, template_folder=str(template_dir), static_folder=str(static_dir)
    )
    app.config["TESTING"] = True
    app.config["APP_RELEASE_TAG"] = "v1.1.0"
    app.config["APP_RELEASE_URL"] = (
        "https://github.com/FTacke/corapan-webapp/releases/tag/v1.1.0"
    )
    app.config["APP_VERSION"] = "1.1.0"

    from src.app.extensions import register_extensions
    from src.app.routes import register_blueprints

    register_extensions(app)
    register_blueprints(app)
    register_context_processors(app)

    return app


def test_resolve_app_release_metadata_prefers_release_tag_and_url():
    metadata = resolve_app_release_metadata(
        {
            "APP_RELEASE_TAG": "v1.2.3",
            "APP_RELEASE_URL": "https://github.com/example/project/releases/tag/v1.2.3",
            "APP_REPOSITORY_URL": "https://github.com/example/project.git",
        }
    )

    assert metadata["app_version"] == "1.2.3"
    assert metadata["app_release_tag"] == "v1.2.3"
    assert metadata["app_release_url"] == "https://github.com/example/project/releases/tag/v1.2.3"


def test_resolve_app_release_metadata_derives_url_from_release_tag_when_missing():
    metadata = resolve_app_release_metadata(
        {
            "APP_RELEASE_TAG": "1.2.4",
            "APP_REPOSITORY_URL": "https://github.com/example/project.git",
        }
    )

    assert metadata["app_version"] == "1.2.4"
    assert metadata["app_release_tag"] == "v1.2.4"
    assert metadata["app_release_url"] == "https://github.com/example/project/releases/tag/v1.2.4"


def test_resolve_app_release_metadata_ignores_malformed_release_url_when_tag_exists():
    metadata = resolve_app_release_metadata(
        {
            "APP_RELEASE_TAG": "v1.0.1",
            "APP_RELEASE_URL": "https://github.com/FTacke",
            "APP_REPOSITORY_URL": "https://github.com/FTacke/corapan-webapp",
        }
    )

    assert metadata["app_version"] == "1.0.1"
    assert metadata["app_release_tag"] == "v1.0.1"
    assert metadata["app_release_url"] == "https://github.com/FTacke/corapan-webapp/releases/tag/v1.0.1"


def test_footer_renders_release_link_when_version_present():
    app = make_app()

    with app.test_request_context("/"):
        html = render_template("partials/footer.html")

    assert "md3-footer__version-link" in html
    assert "v1.1.0" in html
    assert "Versión 1.1.0 (hacer clic para ver detalles)" in html
    assert "https://github.com/FTacke/corapan-webapp/releases/tag/v1.1.0" in html


def test_footer_omits_release_link_when_version_missing():
    app = make_app()
    app.config["APP_VERSION"] = ""
    app.config["APP_RELEASE_TAG"] = ""
    app.config["APP_RELEASE_URL"] = ""

    with app.test_request_context("/"):
        html = render_template("partials/footer.html")

    assert "md3-footer__version-link" not in html
    assert "hacer clic para ver detalles" not in html