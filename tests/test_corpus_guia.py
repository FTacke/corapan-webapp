from src.app import create_app


def test_corpus_guia_page_available():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    rv = client.get("/corpus/guia")
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    assert "Guía para consultar el corpus CO.RA.PAN" in html
    # Check that BlackLab links are present
    assert "https://blacklab.ivdnt.org/" in html
    assert "https://github.com/INL/BlackLab" in html


def test_nav_drawer_contains_corpus_children():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    rv = client.get("/")
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    # Ensure nav contains 'Corpus' and both children
    assert "Corpus" in html
    assert "Consultar corpus" in html
    assert "/corpus/guia" in html
