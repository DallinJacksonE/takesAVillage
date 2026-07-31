import asyncio

from service.api.websocket.connection_manager import ConnectionManager
from service.game_manager.registry import GameRegistry


class Socket:
    def __init__(self, fails=False):
        self.fails = fails
        self.sent = []
        self.closed = False

    async def send_json(self, message):
        if self.fails:
            raise RuntimeError("closed")
        self.sent.append(message)

    async def close(self, code=None):
        self.closed = True
        self.close_code = code


def test_failed_broadcast_recipient_is_removed_without_blocking_others():
    registry = GameRegistry()
    manager = ConnectionManager(registry)
    good, bad = Socket(), Socket(fails=True)
    manager.active_connections["game-1"] = {"good": good, "bad": bad}

    asyncio.run(manager.broadcast_to_game({"event": "ok"}, "game-1"))

    assert good.sent == [{"event": "ok"}]
    assert "bad" not in manager.active_connections["game-1"]


def test_old_disconnect_does_not_remove_replacement_connection():
    registry = GameRegistry()
    manager = ConnectionManager(registry)
    old_socket, replacement = Socket(), Socket()

    asyncio.run(manager.connect(old_socket, "game-1", "player-1"))
    asyncio.run(manager.connect(replacement, "game-1", "player-1"))
    disconnected = manager.disconnect(old_socket, "game-1", "player-1")

    assert disconnected is False
    assert old_socket.closed is True
    assert old_socket.close_code == 4001
    assert manager.active_connections["game-1"]["player-1"] is replacement


def test_failed_stale_broadcast_does_not_remove_replacement_or_player():
    class Game:
        def __init__(self):
            self.removed = []

        def remove_player(self, user_id):
            self.removed.append(user_id)

    class Registry:
        def __init__(self, game):
            self.game = game

        def get(self, _game_id):
            return self.game

    class ReplacedSocket(Socket):
        async def send_json(self, message):
            manager.active_connections["game-1"]["player-1"] = replacement
            raise RuntimeError("stale socket closed")

    game = Game()
    manager = ConnectionManager(Registry(game))
    replacement = Socket()
    stale = ReplacedSocket()
    manager.active_connections["game-1"] = {"player-1": stale}

    asyncio.run(manager.broadcast_to_game({"event": "update"}, "game-1"))

    assert manager.active_connections["game-1"]["player-1"] is replacement
    assert game.removed == []


def test_failed_broadcast_does_not_remove_player_from_running_game():
    class Game:
        status = "RUNNING"

        def __init__(self):
            self.removed = []

        def remove_player(self, user_id):
            self.removed.append(user_id)

    class Registry:
        def __init__(self, game):
            self.game = game

        def get(self, _game_id):
            return self.game

    game = Game()
    manager = ConnectionManager(Registry(game))
    manager.active_connections["game-1"] = {"player-1": Socket(fails=True)}

    asyncio.run(manager.broadcast_to_game({"event": "update"}, "game-1"))

    assert "game-1" not in manager.active_connections
    assert game.removed == []
