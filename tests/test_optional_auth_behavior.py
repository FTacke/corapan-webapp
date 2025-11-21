from werkzeug.security import generate_password_hash
from src.app import create_app
from src.app.routes import auth as auth_routes
from src.app.auth import Role


def test_login_and_optional_auth_routes_set_g_user():
    app = create_app()
    app.config["TESTING"] = True
    # Ensure we require cookies for testing
    client = app.test_client()

    # Create a temporary test credential
    username = "testuser"
    password = "secret123"
    password_hash = generate_password_hash(password)
    auth_routes.CREDENTIALS[username] = auth_routes.Credential(
        role=Role.USER, password_hash=password_hash
    )

    # POST login
    rv = client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    # Successful login returns 303 or HX redirect 204, but cookies should be set in response
    assert rv.status_code in (204, 303, 200)
    # Ensure the session endpoint recognizes authentication (after login cookie set)
    rv_session_post = client.get("/auth/session")
    assert rv_session_post.status_code == 200
    data = rv_session_post.get_json()
    assert data["authenticated"] is True

    # Now call /auth/session - should show authenticated true
    rv2 = client.get("/auth/session")
    assert rv2.status_code == 200
    data = rv2.get_json()
    assert data["authenticated"] is True

    # Now GET /search/advanced and ensure top-app-bar records data-auth true
    rv3 = client.get("/search/advanced")
    assert rv3.status_code == 200
    html = rv3.get_data(as_text=True)
    assert 'data-element="top-app-bar"' in html
    # Find data-auth attribute - should be true
    assert 'data-auth="true"' in html
