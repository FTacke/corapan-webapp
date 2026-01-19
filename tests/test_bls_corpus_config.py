"""Test BlackLab corpus configuration helpers."""

import importlib


def test_build_bls_corpus_path_uses_env(monkeypatch):
    monkeypatch.setenv("BLS_CORPUS", "index")
    monkeypatch.setenv("BLS_BASE_URL", "http://example.com/blacklab-server")

    import src.app.extensions.http_client as http_client

    reloaded = importlib.reload(http_client)
    assert reloaded.BLS_CORPUS == "index"
    assert reloaded.build_bls_corpus_path("hits") == "/corpora/index/hits"
