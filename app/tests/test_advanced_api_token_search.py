import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

os.environ.setdefault("CORAPAN_RUNTIME_ROOT", str(Path(__file__).resolve().parents[2]))
os.environ.setdefault(
    "CORAPAN_MEDIA_ROOT", str(Path(__file__).resolve().parents[2] / "media")
)
os.environ.setdefault("BLS_BASE_URL", "http://localhost:8081/blacklab-server")
os.environ.setdefault("BLS_CORPUS", "corapan")

from src.app.search.advanced_api import (
    _build_token_search_cql,
    _parse_token_ids_raw,
    bp,
)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_parse_token_ids_raw_preserves_case():
    token_ids = _parse_token_ids_raw(" PER1101faa0f,\nURY5bbf88c76 ; mixedCase123 ")

    assert token_ids == ["PER1101faa0f", "URY5bbf88c76", "mixedCase123"]


def test_build_token_search_cql_preserves_case_for_multiple_ids():
    cql = _build_token_search_cql(["PER1101faa0f", "URY5bbf88c76"])

    assert cql == '[tokid="PER1101faa0f" | tokid="URY5bbf88c76"]'


def test_token_search_endpoint_uses_exact_case_in_bls_query(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "summary": {"resultsStats": {"hits": 0}},
        "hits": [],
        "docInfos": {},
    }

    with patch("src.app.search.advanced_api._make_bls_request") as mock_bls:
        mock_bls.return_value = mock_response

        response = client.post(
            "/search/advanced/token/search",
            json={
                "draw": 1,
                "start": 0,
                "length": 25,
                "token_ids_raw": "PER1101faa0f URY5bbf88c76",
                "context_size": 40,
            },
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["recordsFiltered"] == 0

    mock_bls.assert_called_once()
    _, params = mock_bls.call_args.args
    assert params["patt"] == '[tokid="PER1101faa0f" | tokid="URY5bbf88c76"]'