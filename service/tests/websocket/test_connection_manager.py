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


def test_changed_state_broadcasts_are_revisioned_and_ordered():
    class Game:
        id = "game-1"
        status = "RUNNING"

        def __init__(self):
            self.state_revision = 0

        def get_state_for_player(self, user_id):
            return {
                "me": {"id": user_id},
                "state_revision": self.state_revision,
            }

    class Registry:
        def __init__(self, game):
            self.game = game

        def get(self, _game_id):
            return self.game

    class BlockingSocket(Socket):
        def __init__(self):
            super().__init__()
            self.first_send_started = asyncio.Event()
            self.release_first_send = asyncio.Event()

        async def send_json(self, message):
            if not self.sent:
                self.first_send_started.set()
                await self.release_first_send.wait()
            self.sent.append(message)

    async def scenario():
        game = Game()
        socket = BlockingSocket()
        manager = ConnectionManager(Registry(game))
        manager.active_connections[game.id] = {"player-1": socket}

        first = asyncio.create_task(
            manager.broadcast_game_state(game.id, game, changed=True)
        )
        await socket.first_send_started.wait()
        second = asyncio.create_task(
            manager.broadcast_game_state(game.id, game, changed=True)
        )
        await asyncio.sleep(0)

        assert socket.sent == []
        socket.release_first_send.set()
        await asyncio.gather(first, second)

        assert [
            packet["data"]["state_revision"] for packet in socket.sent
        ] == [1, 2]

    asyncio.run(scenario())


def test_recovery_broadcast_reuses_current_revision():
    class Game:
        id = "game-1"
        status = "RUNNING"
        state_revision = 7

        def get_state_for_player(self, user_id):
            return {
                "me": {"id": user_id},
                "state_revision": self.state_revision,
            }

    game = Game()
    socket = Socket()
    manager = ConnectionManager(type("Registry", (), {
        "get": lambda _self, _game_id: game,
    })())
    manager.active_connections[game.id] = {"player-1": socket}

    asyncio.run(manager.broadcast_game_state(game.id, game, changed=False))

    assert game.state_revision == 7
    assert socket.sent[0]["data"]["state_revision"] == 7


def test_personal_state_recovery_waits_for_in_flight_broadcast():
    class Game:
        id = "game-1"
        status = "RUNNING"
        state_revision = 0

        def get_state_for_player(self, user_id):
            return {
                "me": {"id": user_id},
                "state_revision": self.state_revision,
            }

    class BlockingSocket(Socket):
        def __init__(self):
            super().__init__()
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def send_json(self, message):
            if not self.sent:
                self.started.set()
                await self.release.wait()
            self.sent.append(message)

    async def scenario():
        game = Game()
        socket = BlockingSocket()
        manager = ConnectionManager(type("Registry", (), {
            "get": lambda _self, _game_id: game,
        })())
        manager.active_connections[game.id] = {"player-1": socket}

        broadcast = asyncio.create_task(
            manager.broadcast_game_state(game.id, game, changed=True)
        )
        await socket.started.wait()
        recovery = asyncio.create_task(
            manager.send_game_state(game.id, game, "player-1")
        )
        await asyncio.sleep(0)
        assert socket.sent == []

        socket.release.set()
        await asyncio.gather(broadcast, recovery)
        assert len(socket.sent) == 2
        assert [
            packet["data"]["state_revision"] for packet in socket.sent
        ] == [1, 1]

    asyncio.run(scenario())
