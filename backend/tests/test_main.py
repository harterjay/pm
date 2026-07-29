from fastapi.testclient import TestClient

from app.main import STATIC_DIR, app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_built_frontend():
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == (STATIC_DIR / "index.html").read_text(encoding="utf-8")
