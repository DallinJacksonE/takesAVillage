import os
import sys
import unittest

BOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BOTS_DIR, ".."))
for path in (BOTS_DIR, ROOT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from bots.fitness import calculate_fitness, calculate_fitness_report


class FitnessSurvivalPriorityTests(unittest.TestCase):
    def test_later_survival_outweighs_early_resource_hoarding(self):
        early_rich_death = {
            "day": 2,
            "game_length": 15,
            "me": {
                "health": "dead",
                "resources": {"food": 50, "wood": 50, "iron": 50},
                "developments": [],
            },
        }
        late_poor_death = {
            "day": 12,
            "game_length": 15,
            "me": {
                "health": "dead",
                "resources": {"food": 0, "wood": 0, "iron": 0},
                "developments": [],
            },
        }

        self.assertGreater(
            calculate_fitness(late_poor_death),
            calculate_fitness(early_rich_death),
        )

    def test_alive_at_same_day_beats_dead_at_same_day(self):
        dead_state = {
            "day": 8,
            "game_length": 15,
            "me": {
                "health": "dead",
                "resources": {"food": 10, "wood": 10, "iron": 10},
                "developments": [],
            },
        }
        alive_state = {
            "day": 8,
            "game_length": 15,
            "me": {
                "health": "healthy",
                "resources": {"food": 0, "wood": 0, "iron": 0},
                "developments": [],
            },
        }

        self.assertGreater(calculate_fitness(alive_state), calculate_fitness(dead_state))


    def test_fitness_report_rewards_village_success_components(self):
        productive_state = {
            "day": 15,
            "game_length": 15,
            "player_list": [
                {"id": "bot-1", "health": "healthy", "resources": {"food": 4, "wood": 3, "iron": 2}, "developments": ["farm-1", "mine-1"]},
                {"id": "bot-2", "health": "dead", "resources": {"food": 0, "wood": 0, "iron": 0}, "developments": []},
            ],
            "developments": [
                {"id": "farm-1", "owner_id": "bot-1", "level": 3, "maintenance_days": 4},
                {"id": "mine-1", "owner_id": "bot-1", "level": 2, "maintenance_days": 2},
            ],
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 4, "wood": 3, "iron": 2},
                "developments": ["farm-1", "mine-1"],
                "timeline": [
                    {"type": "ACTION_COMPLETED", "data": {"action": "COMMIT_WORK"}},
                    {"type": "TRADE_RESOLVED", "data": {"sent": {"wood": 1}, "received": {"food": 2}}},
                    {"type": "JOINED_FIRE", "data": {"host": "bot-2"}},
                    {"type": "ACTION_COMPLETED", "data": {"action": "CONTEST", "side": "OWNER"}},
                ],
                "trade_history": [
                    {"actual_sent": {"wood": 1}, "actual_received": {"food": 2}},
                ],
                "actions": [
                    {"type": "TRADE", "status": "FINALIZED"},
                ],
            },
        }

        report = calculate_fitness_report(productive_state)

        self.assertGreater(report.components["resources"], 0)
        self.assertGreater(report.components["developments_owned"], 0)
        self.assertGreater(report.components["development_levels"], 0)
        self.assertGreater(report.components["maintenance"], 0)
        self.assertGreater(report.components["successful_work"], 0)
        self.assertGreater(report.components["profitable_trades"], 0)
        self.assertGreater(report.components["fulfilled_contracts"], 0)
        self.assertGreater(report.components["campfire_cooperation"], 0)
        self.assertGreater(report.components["contest_outcomes"], 0)
        self.assertGreater(report.components["relative_ranking"], 0)
        self.assertIn("resources", report.stats)
        self.assertEqual(report.stats["developments_owned"], 2)
        self.assertEqual(calculate_fitness(productive_state), report.score)

    def test_fitness_report_penalizes_illegal_noop_and_repeated_finish_events(self):
        state = {
            "day": 3,
            "game_length": 15,
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 1, "wood": 1, "iron": 0},
                "developments": [],
                "timeline": [
                    {"type": "ILLEGAL_ACTION", "data": {}},
                    {"type": "NO_OP", "data": {}},
                    {"type": "ACTION_COMPLETED", "data": {"action": "FINISH_PHASE"}},
                    {"type": "ACTION_COMPLETED", "data": {"action": "FINISH_PHASE"}},
                    {"type": "ACTION_COMPLETED", "data": {"action": "FINISH_PHASE"}},
                ],
            },
        }

        report = calculate_fitness_report(state)

        self.assertLess(report.components["behavior_penalty"], 0)
        self.assertEqual(report.stats["illegal_action_count"], 1)
        self.assertEqual(report.stats["no_op_count"], 1)
        self.assertEqual(report.stats["finish_phase_count"], 3)


if __name__ == "__main__":
    unittest.main()
