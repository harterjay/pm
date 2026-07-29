from app.ai import AddCardAction, ChatReply, MoveCardAction


class _FakeParseResponse:
    def __init__(self, parsed_output):
        self.parsed_output = parsed_output


class _FakeMessages:
    def __init__(self, parsed_output):
        self._parsed_output = parsed_output

    def parse(self, **kwargs):
        return _FakeParseResponse(self._parsed_output)


class _FakeAnthropicClient:
    def __init__(self, parsed_output):
        self.messages = _FakeMessages(parsed_output)


def _stub_anthropic(monkeypatch, parsed_output):
    import app.ai as ai_module

    monkeypatch.setattr(
        ai_module.anthropic, "Anthropic", lambda *a, **kw: _FakeAnthropicClient(parsed_output)
    )


def test_chat_requires_auth(client):
    response = client.post(
        "/api/ai/chat",
        json={"board": {"columns": [], "cards": {}}, "message": "hello"},
    )
    assert response.status_code == 401


def test_chat_answers_a_question_without_changing_the_board(logged_in_client):
    board = logged_in_client.get("/api/board").json()

    response = logged_in_client.post(
        "/api/ai/chat",
        json={
            "board": board,
            "message": "How many columns are on this board? Answer in one short sentence, and do not change the board.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reply"]
    assert data["board"] == board


def test_chat_moves_a_card_per_the_success_criteria_example(logged_in_client):
    board = logged_in_client.get("/api/board").json()

    response = logged_in_client.post(
        "/api/ai/chat",
        json={"board": board, "message": "Move the roadmap card to Done"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reply"]

    done_column = next(c for c in data["board"]["columns"] if c["id"] == "col-done")
    assert "card-1" in done_column["cardIds"]
    backlog_column = next(c for c in data["board"]["columns"] if c["id"] == "col-backlog")
    assert "card-1" not in backlog_column["cardIds"]


def test_chat_applies_an_add_card_action_and_matches_the_returned_board(
    logged_in_client, monkeypatch
):
    board = logged_in_client.get("/api/board").json()
    _stub_anthropic(
        monkeypatch,
        ChatReply(
            reply="Added it!",
            action=AddCardAction(
                type="add_card", column_id="col-review", title="From the AI", details="Note"
            ),
        ),
    )

    response = logged_in_client.post(
        "/api/ai/chat", json={"board": board, "message": "Add a card to review"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Added it!"

    review_column = next(c for c in data["board"]["columns"] if c["id"] == "col-review")
    new_card_id = review_column["cardIds"][-1]
    assert data["board"]["cards"][new_card_id]["title"] == "From the AI"

    # The applied action is reflected by fetching the board directly too.
    fetched = logged_in_client.get("/api/board").json()
    assert fetched == data["board"]


def test_chat_handles_an_unparseable_response_gracefully(logged_in_client, monkeypatch):
    board = logged_in_client.get("/api/board").json()
    _stub_anthropic(monkeypatch, None)

    response = logged_in_client.post(
        "/api/ai/chat", json={"board": board, "message": "hello"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reply"]
    assert data["board"] == board


def test_chat_ignores_an_action_referencing_a_nonexistent_card(logged_in_client, monkeypatch):
    board = logged_in_client.get("/api/board").json()
    _stub_anthropic(
        monkeypatch,
        ChatReply(
            reply="Moved it.",
            action=MoveCardAction(
                type="move_card", card_id="card-999", column_id="col-done", position=0
            ),
        ),
    )

    response = logged_in_client.post(
        "/api/ai/chat", json={"board": board, "message": "move a card that does not exist"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Moved it."
    assert data["board"] == board
