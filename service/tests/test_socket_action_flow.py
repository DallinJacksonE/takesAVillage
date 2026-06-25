import asyncio
import os
import sys
import types
import unittest

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path = [path for path in sys.path if path != SERVICE_DIR]
sys.path.insert(0, SERVICE_DIR)

httpx_stub = types.ModuleType("httpx")
setattr(httpx_stub, "AsyncClient", object)
sys.modules["httpx"] = httpx_stub

fastapi_stub = types.ModuleType("fastapi")

class _Router:
    def websocket(self, *_args, **_kwargs):
        def decorator(fn):
            return fn
        return decorator

setattr(fastapi_stub, "APIRouter", _Router)
setattr(fastapi_stub, "WebSocket", object)
setattr(fastapi_stub, "WebSocketDisconnect", Exception)
sys.modules["fastapi"] = fastapi_stub

game_manager_stub = types.ModuleType("game_manager")
setattr(game_manager_stub, "active_games", {})
sys.modules["game_manager"] = game_manager_stub

logger_stub = types.ModuleType("logger")

class _Logger:
    def __init__(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def exception(self, *_args, **_kwargs):
        pass

setattr(logger_stub, "BackendLogger", _Logger)
sys.modules["logger"] = logger_stub

import sockets


class _Player:
    def __init__(self):
        self.session_id = "player-1"
        self.health = "healthy"
        self.finished_phase = False


class _Game:
    def __init__(self):
        self.status = "RUNNING"
        self.players = {"player-1": _Player()}
        self.handled_actions = 0

    def handle_action(self, user_id, payload):
        player = self.players[user_id]
        if payload.get("action_command") == "FINISH_PHASE":
            self.handled_actions += 1
            player.finished_phase = True
            return True
        return False


class _Manager:
    def __init__(self):
        self.broadcasts = 0
        self.errors = 0

    async def broadcast_game_state(self, game_id, game):
        self.broadcasts += 1

    async def send_personal_message(self, message, game_id, user_id):
        if message.get("event") == "error":
            self.errors += 1


class SocketActionFlowTests(unittest.TestCase):
    def test_duplicate_finish_phase_is_backend_noop_without_broadcast_or_error(self):
        original_manager = sockets.manager
        manager = _Manager()
        sockets.manager = manager
        game = _Game()
        payload = {"action_command": "FINISH_PHASE", "payload": {}}

        try:
            asyncio.run(sockets.process_game_event("submit_action", payload, "game-1", "player-1", game))
            asyncio.run(sockets.process_game_event("submit_action", payload, "game-1", "player-1", game))
        finally:
            sockets.manager = original_manager

        self.assertEqual(manager.broadcasts, 1)
        self.assertEqual(manager.errors, 0)
        self.assertEqual(game.handled_actions, 1)


if __name__ == "__main__":
    unittest.main()
