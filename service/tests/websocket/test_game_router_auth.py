from fastapi import FastAPI
from fastapi.testclient import TestClient

from service.api.websocket.connection_manager import ConnectionManager
from service.api.websocket.game_router import create_router
from service.db.memory import InMemoryDB
from service.game_manager.lifecycle import GameLifecycleService
from service.game_manager.registry import GameRegistry


def _context():
    database = InMemoryDB()
    registry = GameRegistry()
    lifecycle = GameLifecycleService(registry)
    manager = ConnectionManager(registry)
    app = FastAPI()
    app.include_router(create_router(registry, manager, database))
    client = TestClient(app)
    return client, database, registry, lifecycle, manager


def _join(websocket, user_id, game_id, **extra):
    websocket.send_json({
        "event": "join_room",
        "data": {"userId": user_id, "gameId": game_id, **extra},
    })


def test_websocket_rejects_missing_session_claiming_host_identity():
    client, database, _registry, lifecycle, manager = _context()
    database.create_user("host", True)
    game_id = lifecycle.create_game("host", "default")

    with client.websocket_connect("/ws") as websocket:
        _join(websocket, "host", game_id)
        packet = websocket.receive_json()

    assert packet == {
        "event": "error",
        "data": {"message": "WebSocket authentication failed."},
    }
    assert manager.active_connections == {}


def test_websocket_rejects_valid_session_claiming_another_user():
    client, database, _registry, lifecycle, manager = _context()
    database.create_user("host", True)
    database.create_user("attacker", True)
    game_id = lifecycle.create_game("host", "default")
    client.cookies.set("user_session", "attacker")

    with client.websocket_connect("/ws") as websocket:
        _join(websocket, "host", game_id)
        packet = websocket.receive_json()

    assert packet["data"]["message"] == "WebSocket authentication failed."
    assert manager.active_connections == {}


def test_websocket_rejects_non_member_joining_running_game():
    client, database, registry, lifecycle, manager = _context()
    database.create_user("host", True)
    database.create_user("player", True)
    game_id = lifecycle.create_game("host", "default")
    registry.get(game_id).status = "RUNNING"
    client.cookies.set("user_session", "player")

    with client.websocket_connect("/ws") as websocket:
        _join(websocket, "player", game_id)
        packet = websocket.receive_json()

    assert packet == {
        "event": "error",
        "data": {"message": "Player is not a member of this game."},
    }
    assert manager.active_connections == {}


def test_websocket_requires_bot_secret_for_registered_bot(monkeypatch):
    monkeypatch.setenv("BOT_SECRET", "test-secret")
    client, _database, registry, lifecycle, manager = _context()
    game_id = lifecycle.create_game("host", "default")
    registry.get(game_id).add_player("bot_1234")

    with client.websocket_connect("/ws") as websocket:
        _join(websocket, "bot_1234", game_id, botSecret="wrong")
        packet = websocket.receive_json()

    assert packet["data"]["message"] == "WebSocket authentication failed."
    assert manager.active_connections == {}


def test_websocket_accepts_matching_human_session():
    client, database, _registry, lifecycle, manager = _context()
    database.create_user("host", True)
    game_id = lifecycle.create_game("host", "default")
    client.cookies.set("user_session", "host")

    with client.websocket_connect("/ws") as websocket:
        _join(websocket, "host", game_id)
        packets = [websocket.receive_json(), websocket.receive_json()]
        assert {packet["event"] for packet in packets} == {"chat_history", "game_state"}
        assert manager.active_connections[game_id]["host"] is not None

    assert manager.active_connections == {}


def test_websocket_rejects_malformed_packet_without_dropping_connection():
    client, database, _registry, lifecycle, manager = _context()
    database.create_user("host", True)
    game_id = lifecycle.create_game("host", "default")
    client.cookies.set("user_session", "host")

    with client.websocket_connect("/ws") as websocket:
        _join(websocket, "host", game_id)
        for _ in range(4):
            websocket.receive_json()

        websocket.send_json([])
        assert websocket.receive_json() == {
            "event": "error",
            "data": {"message": "Invalid WebSocket packet."},
        }
        websocket.send_json({"event": "request_update", "data": {}})
        assert websocket.receive_json()["event"] == "game_state"
        assert manager.active_connections[game_id]["host"] is not None
