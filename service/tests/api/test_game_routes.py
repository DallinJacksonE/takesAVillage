import os
from types import SimpleNamespace

def test_new_game_and_active_games_preserve_frontend_contract(api_context):
    client, _database = api_context
    consent = client.post("/api/consent")
    user_id = consent.json()["userId"]

    created = client.post("/api/newGame", json={"ruleset": "default", "botCount": 0})

    assert created.status_code == 200
    game_id = created.json()["gameId"]
    assert game_id.startswith("g_")

    active = client.get("/api/activeGames")

    assert active.status_code == 200
    assert active.json() == {
        "games": [{
            "id": game_id,
            "name": f"Village {game_id}",
            "players": "0/10",
            "isRejoinable": False,
        }]
    }
    assert user_id not in _database.registry.get(game_id).players


def test_new_game_options_expose_default_and_wealthy_rulesets(api_context):
    client, _database = api_context

    response = client.get("/api/newGame")

    assert response.status_code == 200
    assert {"default", "wealthy"}.issubset(response.json()["options"])
    assert "STARTING_INVENTORY" in response.json()["options"]["default"]


def test_join_game_returns_not_found_for_unknown_game(api_context):
    client, _database = api_context

    response = client.post("/api/joinGame", json={"gameId": "missing"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"


def test_bot_join_requires_secret_and_returns_bot_identity(api_context, monkeypatch):
    client, _database = api_context
    game = SimpleNamespace(status="WAITING", added=[])
    game.add_player = game.added.append
    _database.registry.add("game-1", game)
    monkeypatch.setenv("BOT_SECRET", "test-secret")

    denied = client.post(
        "/api/botJoinGame",
        json={"gameId": "game-1", "botSecret": "wrong"},
    )
    joined = client.post(
        "/api/botJoinGame",
        json={"gameId": "game-1", "botSecret": os.environ["BOT_SECRET"]},
    )

    assert denied.status_code == 403
    assert joined.status_code == 200
    assert joined.json()["gameId"] == "game-1"
    assert joined.json()["userId"].startswith("bot_")
    assert game.added == [joined.json()["userId"]]


def test_bot_join_fails_closed_when_secret_is_not_configured(api_context, monkeypatch):
    client, _database = api_context
    game = SimpleNamespace(status="WAITING", added=[])
    game.add_player = game.added.append
    _database.registry.add("game-1", game)
    monkeypatch.delenv("BOT_SECRET", raising=False)

    response = client.post(
        "/api/botJoinGame",
        json={"gameId": "game-1", "botSecret": "default_dev_secret"},
    )

    assert response.status_code == 403
    assert game.added == []
