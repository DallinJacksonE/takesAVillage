import os
import sys
import types
import unittest

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(SERVICE_DIR, ".."))
for path in (SERVICE_DIR, ROOT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from serializers.state_builder import build_player_state


class _Player:
    def __init__(self):
        self.session_id = "player-1"

    def to_dict(self):
        return {
            "id": self.session_id,
            "health": "healthy",
            "resources": {"food": 1, "wood": 1, "iron": 0},
            "actions": [],
            "available_work": [],
            "developments": [],
            "fire_status": "COLD",
            "fire_guests": [],
            "finished_phase": False,
            "timeline": [],
            "trade_history": [],
            "committed_action": None,
        }


class StateBuilderTests(unittest.TestCase):
    def test_player_state_includes_game_length_for_agent_fitness_context(self):
        player = _Player()
        game = types.SimpleNamespace(
            players={player.session_id: player},
            map_data={},
            developments={},
            chats=[],
            status="RUNNING",
            host_id="host",
            day=4,
            game_length=15,
            phase="WORK",
            host_connected=True,
            training=True,
            rules=types.SimpleNamespace(
                DEVELOPMENT_COSTS={},
                MAX_FIRE_SEATS=3,
                CAMPFIRE_COST={"wood": 1},
                COLD_SICKNESS_INCREASE=0.1,
                HUNGER_SICKNESS_INCREASE=0.2,
                RECOVERY_RATE=0.07,
            ),
            get_time_remaining=lambda: 30,
        )

        state = build_player_state(game, player.session_id)

        self.assertEqual(state["game_length"], 15)


if __name__ == "__main__":
    unittest.main()
