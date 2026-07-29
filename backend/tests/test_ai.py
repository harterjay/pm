def test_ask_ai_returns_correct_answer(logged_in_client):
    response = logged_in_client.post(
        "/api/ai/ask", json={"prompt": "What is 2+2? Reply with just the number."}
    )
    assert response.status_code == 200
    assert "4" in response.json()["reply"]


def test_ask_ai_requires_auth(client):
    response = client.post("/api/ai/ask", json={"prompt": "hello"})
    assert response.status_code == 401


def test_ask_ai_handles_missing_api_key(logged_in_client, monkeypatch):
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE"):
        monkeypatch.delenv(var, raising=False)

    response = logged_in_client.post("/api/ai/ask", json={"prompt": "hello"})
    assert response.status_code == 502


def test_ask_ai_handles_invalid_api_key(logged_in_client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-invalid-test-key")

    response = logged_in_client.post("/api/ai/ask", json={"prompt": "hello"})
    assert response.status_code == 502
