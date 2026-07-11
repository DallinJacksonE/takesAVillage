<<<<<<< HEAD
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
=======
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

sys.modules.pop("db", None)
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

    def test_in_memory_training_games_include_status_and_counts(self):
        database = research_db.InMemoryDB()
        database.create_training_batch(
            "batch-1",
            {
                "ruleset": "default",
                "bot_model": "GOAPGenetic",
                "bot_count": 4,
                "total_generations": 2,
                "base_genome_id": "random",
                "config": {"games_per_generation": 5},
            },
        )

        database.mark_training_batch_game_started("batch-1", "game-1", 1)
        database.mark_training_batch_game_failed("batch-1", "game-1", "bot spawn timeout")

        games = database.get_training_games("batch-1")
        batch = database.get_training_batch("batch-1")

        self.assertEqual(games, [{
            "game_id": "game-1",
            "generation": 1,
            "attempt": None,
            "status": "failed",
            "error_message": "bot spawn timeout",
            "genome_count": 0,
            "best_fitness": None,
            "average_fitness": None,
        }])
        self.assertEqual(batch["games_completed"], 1)
        self.assertEqual(batch["games_failed"], 1)

    def test_in_memory_training_game_attempt_moves_from_spawning_to_running(self):
        database = research_db.InMemoryDB()
        database.create_training_batch(
            "batch-1",
            {
                "ruleset": "default",
                "bot_model": "GOAPGenetic",
                "bot_count": 4,
                "total_generations": 2,
                "base_genome_id": "random",
                "config": {"games_per_generation": 5},
            },
        )

        database.mark_training_batch_game_started("batch-1", "game-1", 1)
        self.assertEqual(database.get_training_games("batch-1")[0]["status"], "spawning")

        database.mark_training_batch_game_running("batch-1", "game-1")

        self.assertEqual(database.get_training_games("batch-1")[0]["status"], "running")

    def test_in_memory_training_game_attempt_records_attempt_index(self):
        database = research_db.InMemoryDB()
        database.create_training_batch(
            "batch-1",
            {
                "ruleset": "default",
                "bot_model": "GOAPGenetic",
                "bot_count": 4,
                "total_generations": 2,
                "base_genome_id": "random",
                "config": {"games_per_generation": 5},
            },
        )

        database.mark_training_batch_game_started(
            "batch-1", "game-3", 1, attempt=3)

        games = database.get_training_games("batch-1")

        self.assertEqual(games[0]["attempt"], 3)

    def test_in_memory_training_game_attempt_can_be_completed_with_fitness_summary(self):
        database = research_db.InMemoryDB()
        database.create_training_batch(
            "batch-1",
            {
                "ruleset": "default",
                "bot_model": "GOAPGenetic",
                "bot_count": 4,
                "total_generations": 2,
                "base_genome_id": "random",
                "config": {"games_per_generation": 5},
            },
        )

        database.mark_training_batch_game_started("batch-1", "game-1", 1)
        database.mark_training_batch_game_completed(
            "batch-1",
            "game-1",
            genome_count=3,
            fitness_summary={"best_fitness": 12.0, "average_fitness": 8.5},
        )

        games = database.get_training_games("batch-1")
        batch = database.get_training_batch("batch-1")

        self.assertEqual(games[0]["status"], "completed")
        self.assertEqual(games[0]["genome_count"], 3)
        self.assertEqual(games[0]["best_fitness"], 12.0)
        self.assertEqual(games[0]["average_fitness"], 8.5)
        self.assertIsNone(games[0]["error_message"])
        self.assertEqual(batch["games_completed"], 1)
        self.assertEqual(batch["games_failed"], 0)

    def test_in_memory_training_batch_records_heartbeat_and_stalled_status(self):
        database = research_db.InMemoryDB()
        database.create_training_batch(
            "batch-1",
            {
                "ruleset": "default",
                "bot_model": "GOAPGenetic",
                "bot_count": 4,
                "total_generations": 2,
                "base_genome_id": "random",
                "config": {"games_per_generation": 5},
            },
        )

        database.record_training_batch_heartbeat(
            "batch-1",
            phase="spawning",
            current_generation=2,
            current_game_id="game-2",
        )
        database.update_training_batch_status(
            "batch-1",
            "stalled",
            "No heartbeat received before timeout",
        )

        batch = database.get_training_batch("batch-1")

        self.assertEqual(batch["status"], "stalled")
        self.assertEqual(batch["phase"], "spawning")
        self.assertEqual(batch["current_generation"], 2)
        self.assertEqual(batch["current_game_id"], "game-2")
        self.assertEqual(batch["last_error"], "No heartbeat received before timeout")
        self.assertIsNotNone(batch["last_heartbeat_at"])

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

    def test_mysql_training_games_query_selects_contest_and_lie_counts_separately(self):
        source_path = os.path.join(SERVICE_DIR, "db.py")
        with open(source_path, "r", encoding="utf-8") as source_file:
            source = source_file.read()

        self.assertIn("contest_count,\n                    lie_count", source)


if __name__ == "__main__":
    unittest.main()
>>>>>>> 5aae65484608285345edeb4ee838d500ef4f5a69
