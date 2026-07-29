import pytest
from fastapi.testclient import TestClient

from app.main import PASSWORD, STATIC_DIR, USERNAME, app


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


def test_database_file_created_fresh_when_missing(tmp_path, monkeypatch):
    db_path = tmp_path / "fresh.db"
    assert not db_path.exists()
    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    with TestClient(app) as test_client:
        test_client.post("/api/login", json={"username": USERNAME, "password": PASSWORD})
        response = test_client.get("/api/board")
        assert response.status_code == 200

    assert db_path.exists()


def test_database_file_reused_when_present(tmp_path, monkeypatch):
    db_path = tmp_path / "reused.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    with TestClient(app) as test_client:
        test_client.post("/api/login", json={"username": USERNAME, "password": PASSWORD})
        test_client.post(
            "/api/board/columns/col-backlog/cards", json={"title": "Persisted card"}
        )

    created_at_first_run = db_path.stat().st_mtime

    with TestClient(app) as test_client:
        test_client.post("/api/login", json={"username": USERNAME, "password": PASSWORD})
        response = test_client.get("/api/board")

    board = response.json()
    assert any(card["title"] == "Persisted card" for card in board["cards"].values())
    # File wasn't recreated from scratch on the second run.
    assert db_path.stat().st_mtime >= created_at_first_run


def test_get_board_requires_auth(client):
    response = client.get("/api/board")
    assert response.status_code == 401


def test_get_board_returns_seed_data(logged_in_client):
    response = logged_in_client.get("/api/board")
    assert response.status_code == 200
    board = response.json()

    assert [column["id"] for column in board["columns"]] == [
        "col-backlog",
        "col-discovery",
        "col-progress",
        "col-review",
        "col-done",
    ]
    assert board["columns"][0]["cardIds"] == ["card-1", "card-2"]
    assert board["cards"]["card-1"]["title"] == "Align roadmap themes"
    assert len(board["cards"]) == 8


def test_rename_column(logged_in_client):
    response = logged_in_client.patch(
        "/api/board/columns/col-backlog", json={"title": "New Name"}
    )
    assert response.status_code == 200
    board = response.json()
    assert board["columns"][0]["title"] == "New Name"


def test_rename_column_rejects_empty_title(logged_in_client):
    response = logged_in_client.patch("/api/board/columns/col-backlog", json={"title": "   "})
    assert response.status_code == 422


def test_rename_column_not_found(logged_in_client):
    response = logged_in_client.patch(
        "/api/board/columns/col-nonexistent", json={"title": "New Name"}
    )
    assert response.status_code == 404


def test_add_card(logged_in_client):
    response = logged_in_client.post(
        "/api/board/columns/col-review/cards",
        json={"title": "New card", "details": "Some details"},
    )
    assert response.status_code == 200
    board = response.json()
    review_column = next(c for c in board["columns"] if c["id"] == "col-review")
    assert len(review_column["cardIds"]) == 2
    new_card_id = review_column["cardIds"][-1]
    assert board["cards"][new_card_id]["title"] == "New card"
    assert board["cards"][new_card_id]["details"] == "Some details"


def test_add_card_rejects_empty_title(logged_in_client):
    response = logged_in_client.post(
        "/api/board/columns/col-review/cards", json={"title": ""}
    )
    assert response.status_code == 422


def test_add_card_to_nonexistent_column(logged_in_client):
    response = logged_in_client.post(
        "/api/board/columns/col-nonexistent/cards", json={"title": "New card"}
    )
    assert response.status_code == 404


def test_edit_card(logged_in_client):
    response = logged_in_client.patch(
        "/api/board/cards/card-1", json={"title": "Updated", "details": "Updated details"}
    )
    assert response.status_code == 200
    board = response.json()
    assert board["cards"]["card-1"]["title"] == "Updated"
    assert board["cards"]["card-1"]["details"] == "Updated details"


def test_edit_card_rejects_empty_title(logged_in_client):
    response = logged_in_client.patch("/api/board/cards/card-1", json={"title": ""})
    assert response.status_code == 422


def test_edit_card_not_found(logged_in_client):
    response = logged_in_client.patch("/api/board/cards/card-999", json={"title": "x"})
    assert response.status_code == 404


def test_edit_card_invalid_id_format(logged_in_client):
    response = logged_in_client.patch("/api/board/cards/not-a-card-id", json={"title": "x"})
    assert response.status_code == 400


def test_delete_card(logged_in_client):
    response = logged_in_client.delete("/api/board/cards/card-1")
    assert response.status_code == 200
    board = response.json()
    assert "card-1" not in board["cards"]
    backlog_column = next(c for c in board["columns"] if c["id"] == "col-backlog")
    assert backlog_column["cardIds"] == ["card-2"]


def test_delete_card_not_found(logged_in_client):
    response = logged_in_client.delete("/api/board/cards/card-999")
    assert response.status_code == 404


def test_move_card_within_same_column(logged_in_client):
    response = logged_in_client.post(
        "/api/board/cards/card-2/move", json={"columnId": "col-backlog", "position": 0}
    )
    assert response.status_code == 200
    board = response.json()
    backlog_column = next(c for c in board["columns"] if c["id"] == "col-backlog")
    assert backlog_column["cardIds"] == ["card-2", "card-1"]


def test_move_card_across_columns(logged_in_client):
    response = logged_in_client.post(
        "/api/board/cards/card-1/move", json={"columnId": "col-done", "position": 0}
    )
    assert response.status_code == 200
    board = response.json()
    backlog_column = next(c for c in board["columns"] if c["id"] == "col-backlog")
    done_column = next(c for c in board["columns"] if c["id"] == "col-done")
    assert backlog_column["cardIds"] == ["card-2"]
    assert done_column["cardIds"][0] == "card-1"
    assert board["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_move_card_position_is_clamped_to_column_length(logged_in_client):
    response = logged_in_client.post(
        "/api/board/cards/card-1/move", json={"columnId": "col-review", "position": 999}
    )
    assert response.status_code == 200
    board = response.json()
    review_column = next(c for c in board["columns"] if c["id"] == "col-review")
    assert review_column["cardIds"][-1] == "card-1"


def test_move_card_to_nonexistent_column(logged_in_client):
    response = logged_in_client.post(
        "/api/board/cards/card-1/move", json={"columnId": "col-nonexistent", "position": 0}
    )
    assert response.status_code == 404


def test_move_nonexistent_card(logged_in_client):
    response = logged_in_client.post(
        "/api/board/cards/card-999/move", json={"columnId": "col-review", "position": 0}
    )
    assert response.status_code == 404
