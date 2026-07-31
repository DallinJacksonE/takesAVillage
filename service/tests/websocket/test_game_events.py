import asyncio
from types import SimpleNamespace

from service.api.websocket.connection_manager import ConnectionManager
from service.api.websocket.game_events import process_game_event
from service.game_manager.registry import GameRegistry


class RecordingManager:
    def __init__(self):
        self.broadcasts = []
        self.states = []
        self.personal = []

    async def broadcast_to_game(self, message, game_id):
        self.broadcasts.append((message, game_id))

    async def broadcast_game_state(self, game_id, game):
        self.states.append((game_id, game))

    async def send_personal_message(self, message, game_id, user_id):
        self.personal.append((message, game_id, user_id))


class EventGame:
    def __init__(self):
        self.host_id = "host"
        self.status = "WAITING"
        self.players = {
            "host": SimpleNamespace(finished_phase=False),
            "player": SimpleNamespace(finished_phase=False),
        }
        self.chats = []
        self.actions = []
        self.created_chats = []

    def start_game(self):
        self.status = "RUNNING"
        return True

    def get_state_for_player(self, user_id):
        return {"me": {"id": user_id}, "status": self.status}

    def handle_action(self, user_id, payload):
        self.actions.append((user_id, payload))
        return payload.get("accepted", True)

    def handle_chat(self, user_id, payload):
        return SimpleNamespace(
            from_id=user_id,
            to_id=payload.get("to_id", "GLOBAL"),
            to_dict=lambda: {"from_id": user_id, **payload},
        )

    def create_chat(self, user_id, name, member_ids):
        self.created_chats.append((user_id, name, member_ids))
        return object()


def run_event(event, payload, manager, user_id="host", game=None):
    game = game or EventGame()
    asyncio.run(process_game_event(
        event, payload, "game-1", user_id, game, manager
    ))
    return game


def test_start_game_broadcasts_started_event_and_state():
    manager = RecordingManager()

    game = run_event("start_game_request", {}, manager, user_id="host")

    assert game.status == "RUNNING"
    assert manager.broadcasts == [
        ({"event": "game_started", "data": {"day": 1}}, "game-1")
    ]
    assert manager.states == [("game-1", game)]


def test_request_update_sends_player_specific_state():
    manager = RecordingManager()

    run_event("request_update", {}, manager, user_id="player")

    assert manager.personal == [(
        {"event": "game_state", "data": {
            "me": {"id": "player"}, "status": "WAITING"
        }},
        "game-1",
        "player",
    )]


def test_successful_action_broadcasts_state_and_rejected_action_sends_error():
    manager = RecordingManager()
    game = EventGame()
    game.status = "RUNNING"

    run_event("submit_action", {"action_command": "BUILD_DEV", "accepted": True}, manager, "player", game)
    run_event("submit_action", {"action_command": "BUILD_DEV", "accepted": False}, manager, "player", game)

    assert len(manager.states) == 1
    assert manager.personal[-1][0] == {
        "event": "error",
        "data": {
            "message": "Action rejected by game rules.",
            "action_command": "BUILD_DEV",
        },
    }


def test_global_chat_and_chat_creation_are_broadcast():
    manager = RecordingManager()
    game = EventGame()

    run_event("send_chat", {"content": "hello", "to_id": "GLOBAL"}, manager, "player", game)
    run_event(
        "create_chat",
        {"name": "team", "memberIds": ["host", "player"]},
        manager,
        "player",
        game,
    )

    assert manager.broadcasts[0][0]["event"] == "new_chat_message"
    assert manager.broadcasts[0][0]["data"]["content"] == "hello"
    assert game.created_chats == [("player", "team", ["host", "player"])]
    assert manager.states == [("game-1", game)]


def test_connection_manager_disconnect_removes_only_target_connection():
    manager = ConnectionManager(GameRegistry())
    first = object()
    second = object()
    manager.active_connections = {"game-1": {"first": first, "second": second}}

    manager.disconnect(first, "game-1", "first")

    assert manager.active_connections == {"game-1": {"second": second}}
