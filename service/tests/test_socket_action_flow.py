import asyncio
import types
import unittest

from service.api.websocket.game_events import process_game_event


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
        manager = _Manager()
        game = _Game()
        payload = {"action_command": "FINISH_PHASE", "payload": {}}

        asyncio.run(process_game_event(
            "submit_action", payload, "game-1", "player-1", game, manager
        ))
        asyncio.run(process_game_event(
            "submit_action", payload, "game-1", "player-1", game, manager
        ))

        self.assertEqual(manager.broadcasts, 1)
        self.assertEqual(manager.errors, 0)
        self.assertEqual(game.handled_actions, 1)


if __name__ == "__main__":
    unittest.main()
