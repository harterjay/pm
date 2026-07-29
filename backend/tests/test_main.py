import pytest
from fastapi.testclient import TestClient

from app.main import PASSWORD, STATIC_DIR, USERNAME, app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_session_status_when_logged_out(client):
    response = client.get("/api/session")
    assert response.json() == {"authenticated": False}


def test_root_redirects_to_login_when_unauthenticated(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/login"


def test_login_with_wrong_password_is_rejected(client):
    response = client.post("/api/login", json={"username": USERNAME, "password": "wrong"})
    assert response.status_code == 401

    session_response = client.get("/api/session")
    assert session_response.json() == {"authenticated": False}


def test_login_with_correct_credentials_grants_access(client):
    response = client.post("/api/login", json={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 200
    assert response.json() == {"authenticated": True}

    session_response = client.get("/api/session")
    assert session_response.json() == {"authenticated": True}

    root_response = client.get("/")
    assert root_response.status_code == 200
    assert root_response.text == (STATIC_DIR / "index.html").read_text(encoding="utf-8")


def test_login_page_redirects_to_root_when_authenticated(client):
    client.post("/api/login", json={"username": USERNAME, "password": PASSWORD})
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/"


def test_logout_clears_session(client):
    client.post("/api/login", json={"username": USERNAME, "password": PASSWORD})
    logout_response = client.post("/api/logout")
    assert logout_response.json() == {"authenticated": False}

    session_response = client.get("/api/session")
    assert session_response.json() == {"authenticated": False}
