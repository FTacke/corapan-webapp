"""Test BlackLab corpus configuration helpers."""

import importlib.util
from pathlib import Path


def test_build_bls_corpus_path_uses_env(monkeypatch):
    monkeypatch.setenv("BLS_CORPUS", "corapan")
    monkeypatch.setenv("BLS_BASE_URL", "http://example.com/blacklab-server")

    module_path = Path(__file__).resolve().parents[1] / "src" / "app" / "extensions" / "http_client.py"
    spec = importlib.util.spec_from_file_location("http_client_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    http_client = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(http_client)

    assert http_client.BLS_CORPUS == "corapan"
    assert http_client.build_bls_corpus_path("hits") == "/corpora/corapan/hits"
