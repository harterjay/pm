import pytest
from fastapi.testclient import TestClient

from app.main import PASSWORD, USERNAME, app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def logged_in_client(client):
    response = client.post("/api/login", json={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 200
    return client
