import importlib
import os
import sys
import types
import unittest

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

mysql_stub = types.ModuleType("mysql")
connector_stub = types.ModuleType("mysql.connector")
setattr(connector_stub, "Error", Exception)
setattr(connector_stub, "errorcode", types.SimpleNamespace())
setattr(connector_stub, "connect", lambda **_kwargs: None)
setattr(mysql_stub, "connector", connector_stub)
sys.modules["mysql"] = mysql_stub
sys.modules["mysql.connector"] = connector_stub

logger_stub = types.ModuleType("logger")

class _Logger:
    def __init__(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass

setattr(logger_stub, "BackendLogger", _Logger)
sys.modules["logger"] = logger_stub

snapshots_stub = types.ModuleType("serializers.snapshots")
setattr(snapshots_stub, "_safe_serialize", lambda value: value)
sys.modules["serializers.snapshots"] = snapshots_stub

research_db = importlib.import_module("db")


class ResearchPersistenceTests(unittest.TestCase):
    def test_in_memory_training_batch_lifecycle_survives_after_completion(self):
        database = research_db.InMemoryDB()

        database.create_training_batch(
            "batch-1",
            {
                "ruleset": "default",
                "bot_model": "GOAPGenetic",
                "bot_count": 4,
                "total_generations": 2,
                "base_genome_id": "random",
                "config": {"mutation_rate": 0.2},
            },
        )
        database.mark_training_batch_game_started("batch-1", "game-1", 1)
        database.append_training_batch_generation_stats(
            "batch-1",
            {"generation": 1, "best_fitness": 10.0, "average_fitness": 7.5},
        )
        database.complete_training_batch("batch-1", final_champion_genome_id="genome-1")

        batches = database.get_training_batches()
        detail = database.get_training_batch("batch-1")

        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0]["batch_id"], "batch-1")
        self.assertEqual(batches[0]["status"], "completed")
        self.assertEqual(detail["current_game_id"], "game-1")
        self.assertEqual(detail["current_generation"], 1)
        self.assertEqual(detail["generation_statistics"][0]["average_fitness"], 7.5)
        self.assertEqual(detail["final_champion_genome_id"], "genome-1")

    def test_game_result_can_be_linked_to_training_batch(self):
        database = research_db.InMemoryDB()

        database.store_game_result(
            "game-1",
            3,
            "NIGHT",
            {"players": {}, "map": {}},
            training_batch_id="batch-1",
            training_generation=2,
            game_type="training",
        )

        games = database.get_all_games()

        self.assertEqual(games[0]["game_id"], "game-1")
        self.assertEqual(games[0]["training_batch_id"], "batch-1")
        self.assertEqual(games[0]["training_generation"], 2)
        self.assertEqual(games[0]["game_type"], "training")

    def test_research_visualization_storage_returns_metadata_and_bytes(self):
        database = research_db.InMemoryDB()

        visualization_id = database.store_research_visualization(
            scope_type="game",
            scope_id="game-1",
            name="inventory_over_time",
            title="Inventory Over Time",
            mime_type="image/png",
            image_bytes=b"png-bytes",
            metadata={"player_id": "bot-1"},
        )

        visualizations = database.get_research_visualizations("game", "game-1")
        image = database.get_research_visualization(visualization_id)

        self.assertEqual(visualizations[0]["id"], visualization_id)
        self.assertEqual(visualizations[0]["url"], f"/api/research/visualizations/{visualization_id}")
        self.assertNotIn("image_bytes", visualizations[0])
        self.assertEqual(image["image_bytes"], b"png-bytes")
        self.assertEqual(image["metadata"], {"player_id": "bot-1"})

    def test_mysql_schema_avoids_add_column_if_not_exists_before_research_tables(self):
        database = research_db.MySQLDB({"db": {}})

        schema = database._get_schema_script()

        self.assertNotIn("ADD COLUMN IF NOT EXISTS", schema)
        self.assertIn("CREATE TABLE IF NOT EXISTS `research_visualizations`", schema)


if __name__ == "__main__":
    unittest.main()
