import importlib
import asyncio
from datetime import datetime, timedelta
import os
import sys
import types
import unittest

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(SERVICE_DIR, ".."))
BOTS_DIR = os.path.join(ROOT_DIR, "bots")
for path in (SERVICE_DIR, BOTS_DIR, ROOT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

httpx_stub = types.ModuleType("httpx")
setattr(httpx_stub, "AsyncClient", object)
sys.modules["httpx"] = httpx_stub

fastapi_stub = types.ModuleType("fastapi")
setattr(fastapi_stub, "WebSocket", object)
sys.modules["fastapi"] = fastapi_stub

db_stub = types.ModuleType("db")
setattr(db_stub, "db", types.SimpleNamespace(get_all_genomes=lambda: [], store_genome=lambda *args, **kwargs: None))
sys.modules["db"] = db_stub

game_manager_stub = types.ModuleType("game_manager")
setattr(game_manager_stub, "create_game", lambda *args, **kwargs: "test-game")
sys.modules["game_manager"] = game_manager_stub

logger_stub = types.ModuleType("logger")

class _Logger:
    def __init__(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

setattr(logger_stub, "BackendLogger", _Logger)
sys.modules["logger"] = logger_stub

training_orchestrator = importlib.import_module("training_orchestrator")
training_genomes = importlib.import_module("training_genomes")
training_population = importlib.import_module("training_population")
from models.goap_genetic.goap_genome import GOAPGenome


class TrainingOrchestratorGOAPGenomeTests(unittest.TestCase):
    def test_goap_model_uses_goap_specific_fields(self):
        fields = training_genomes.get_genome_fields_for_model("GOAPGenetic")

        self.assertEqual(set(fields), GOAPGenome.recommended_training_field_names())
        self.assertIn("warmth_desperation_weight", fields)
        self.assertIn("sickness_desperation_weight", fields)
        self.assertIn("trade_deception_weight", fields)
        self.assertIn("wage_deception_weight", fields)
        self.assertIn("resource_urgency_curve", fields)
        self.assertIn("action_cost_weight", fields)
        self.assertIn("tie_break_weight", fields)
        self.assertIn("planning_depth_weight", fields)
        self.assertIn("trust_weight", fields)
        self.assertNotEqual(fields, training_genomes.GENOME_FIELDS)

    def test_training_orchestrator_does_not_import_bot_modules(self):
        source_path = os.path.join(SERVICE_DIR, "training_orchestrator.py")
        with open(source_path, "r", encoding="utf-8") as source_file:
            source = source_file.read()

        self.assertNotIn("bots.", source)
        self.assertNotIn("GOAPGenome", source)

    def test_goap_random_genome_values_are_minus_one_to_one(self):
        genome = training_genomes.random_genome_dict_for_model("GOAPGenetic")

        self.assertIn("warmth_desperation_weight", genome)
        for gene_name, gene_value in genome.items():
            self.assertGreaterEqual(gene_value, -1.0, gene_name)
            self.assertLessEqual(gene_value, 1.0, gene_name)

    def test_goap_mutation_clamps_values_to_minus_one_to_one(self):
        genome = {
            field: 1.0
            for field in training_genomes.get_genome_fields_for_model("GOAPGenetic")
        }

        mutant = training_genomes.mutate_genome_for_model(
            "GOAPGenetic",
            genome,
            mutation_strength=100.0,
            mutation_rate=1.0,
        )

        for gene_name, gene_value in mutant.items():
            self.assertGreaterEqual(gene_value, -1.0, gene_name)
            self.assertLessEqual(gene_value, 1.0, gene_name)

    def test_legacy_genetic_model_keeps_existing_zero_to_three_range(self):
        genome = training_genomes.random_genome_dict_for_model("genetic")

        self.assertEqual(set(genome), set(training_genomes.GENOME_FIELDS))
        for gene_name, gene_value in genome.items():
            self.assertGreaterEqual(gene_value, 0.0, gene_name)
            self.assertLessEqual(gene_value, 3.0, gene_name)

    def test_generation_statistics_explain_population_outcomes(self):
        entries = [
            {
                "fitness": 10,
                "stats": {"survived": False, "resources": {"food": 1}, "developments_owned": 0, "illegal_action_count": 2},
                "genome": {"food_weight": 0.0, "wood_weight": 0.0},
            },
            {
                "fitness": 20,
                "stats": {"survived": True, "resources": {"food": 3, "wood": 1}, "developments_owned": 2, "illegal_action_count": 0},
                "genome": {"food_weight": 1.0, "wood_weight": -1.0},
            },
            {
                "fitness": 30,
                "stats": {"survived": True, "resources": {"food": 2, "iron": 2}, "developments_owned": 1, "illegal_action_count": 1},
                "genome": {"food_weight": -1.0, "wood_weight": 1.0},
            },
        ]

        stats = training_population.build_generation_statistics(entries)

        self.assertEqual(stats["best_fitness"], 30.0)
        self.assertEqual(stats["average_fitness"], 20.0)
        self.assertEqual(stats["median_fitness"], 20.0)
        self.assertEqual(stats["worst_fitness"], 10.0)
        self.assertAlmostEqual(stats["survival_rate"], 2 / 3)
        self.assertEqual(stats["average_resources"], 3.0)
        self.assertEqual(stats["average_developments"], 1.0)
        self.assertEqual(stats["illegal_action_count"], 3)
        self.assertGreater(stats["gene_diversity"]["food_weight"], 0)

    def test_next_population_preserves_elites_and_injects_diversity(self):
        entries = [
            {"fitness": 100, "genome": {"food_weight": 1.0}},
            {"fitness": 90, "genome": {"food_weight": 1.0}},
            {"fitness": 80, "genome": {"food_weight": 1.0}},
            {"fitness": 70, "genome": {"food_weight": 1.0}},
        ]

        population = training_population.build_next_population(
            "GOAPGenetic",
            entries,
            bot_count=4,
            elite_count=1,
            selection_size=2,
            mutation_strength=0.0,
            mutation_rate=0.0,
            random_immigrant_count=1,
        )

        self.assertEqual(len(population), 4)
        self.assertEqual(population[0]["food_weight"], 1.0)
        self.assertTrue(
            any(genome["food_weight"] != 1.0 for genome in population[1:]),
            population,
        )


class TrainingOrchestratorRobustnessTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        training_orchestrator.active_training_sessions.clear()
        self.db_calls = []

        def record(name):
            def _recorder(*args, **kwargs):
                self.db_calls.append((name, args, kwargs))
            return _recorder

        training_orchestrator.db.create_training_batch = record("create_training_batch")
        training_orchestrator.db.mark_training_batch_game_started = record("mark_training_batch_game_started")
        training_orchestrator.db.mark_training_batch_game_running = record("mark_training_batch_game_running")
        training_orchestrator.db.append_training_batch_generation_stats = record("append_training_batch_generation_stats")
        training_orchestrator.db.complete_training_batch = record("complete_training_batch")
        training_orchestrator.db.mark_training_batch_game_failed = record("mark_training_batch_game_failed")
        training_orchestrator.db.mark_training_batch_game_completed = record("mark_training_batch_game_completed")
        training_orchestrator.db.record_training_batch_heartbeat = record("record_training_batch_heartbeat")
        training_orchestrator.db.update_training_batch_status = record("update_training_batch_status")
        training_orchestrator.db.store_genome = record("store_genome")

    async def test_start_training_session_accepts_games_per_generation(self):
        posts = []

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def post(self, url, json, timeout):
                posts.append((url, json, timeout))

        original_client = training_orchestrator.httpx.AsyncClient
        original_create_game = training_orchestrator.create_game
        training_orchestrator.httpx.AsyncClient = FakeClient
        training_orchestrator.create_game = lambda **_kwargs: "game-1"
        try:
            session_id = await training_orchestrator.start_training_session(
                "default",
                bot_count=3,
                generations=2,
                base_genome_id="random",
                bot_model="GOAPGenetic",
                games_per_generation=3,
            )
        finally:
            training_orchestrator.httpx.AsyncClient = original_client
            training_orchestrator.create_game = original_create_game

        session = training_orchestrator.active_training_sessions[session_id]
        self.assertEqual(session["games_per_generation"], 3)
        self.assertEqual(session["current_generation_game_index"], 3)
        self.assertEqual(len(posts), 3)
        self.assertEqual(posts[0][1]["botCount"], 3)
        create_call = [call for call in self.db_calls if call[0] == "create_training_batch"][0]
        self.assertEqual(create_call[1][1]["config"]["games_per_generation"], 3)
        running_calls = [call for call in self.db_calls if call[0] == "mark_training_batch_game_running"]
        self.assertEqual(len(running_calls), 3)

    async def test_failed_genome_fetch_counts_failed_game_without_serial_trigger(self):
        triggered = []

        class FakeResponse:
            status_code = 500
            text = "no genomes yet"

            def json(self):
                return {}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def get(self, *_args, **_kwargs):
                return FakeResponse()

        async def fake_trigger(session_id):
            triggered.append(session_id)

        original_client = training_orchestrator.httpx.AsyncClient
        original_trigger = training_orchestrator._trigger_next_game
        training_orchestrator.httpx.AsyncClient = FakeClient
        training_orchestrator._trigger_next_game = fake_trigger
        training_orchestrator.active_training_sessions["session-1"] = {
            "ruleset": "default",
            "bot_count": 2,
            "generations_left": 1,
            "population": [{"food_weight": 1.0}, {"food_weight": 0.0}],
            "generation": 1,
            "elite_count": 1,
            "selection_size": 1,
            "mutation_strength": 0.0,
            "mutation_rate": 0.0,
            "random_immigrant_count": 0,
            "generation_statistics": [],
            "bot_model": "GOAPGenetic",
            "games_per_generation": 2,
            "games_completed": 0,
            "games_failed": 0,
            "fitness_entries": [],
            "games": ["game-1"],
            "all_fitness_entries": [],
        }
        try:
            await training_orchestrator.handle_training_game_ended("game-1", "session-1")
        finally:
            training_orchestrator.httpx.AsyncClient = original_client
            training_orchestrator._trigger_next_game = original_trigger

        session = training_orchestrator.active_training_sessions["session-1"]
        self.assertEqual(session["games_completed"], 1)
        self.assertEqual(session["games_failed"], 1)
        self.assertFalse(session.get("processing_game_end"))
        self.assertEqual(triggered, [])

    async def test_start_training_session_schedules_generation_games_concurrently(self):
        posts = []
        created_game_ids = []

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def post(self, url, json, timeout):
                posts.append((url, json, timeout))

        def fake_create_game(**_kwargs):
            game_id = f"game-{len(created_game_ids) + 1}"
            created_game_ids.append(game_id)
            return game_id

        original_client = training_orchestrator.httpx.AsyncClient
        original_create_game = training_orchestrator.create_game
        training_orchestrator.httpx.AsyncClient = FakeClient
        training_orchestrator.create_game = fake_create_game
        try:
            session_id = await training_orchestrator.start_training_session(
                "default",
                bot_count=3,
                generations=1,
                base_genome_id="random",
                bot_model="GOAPGenetic",
                games_per_generation=3,
            )
            await asyncio.sleep(0)
        finally:
            training_orchestrator.httpx.AsyncClient = original_client
            training_orchestrator.create_game = original_create_game

        self.assertEqual(created_game_ids, ["game-1", "game-2", "game-3"])
        self.assertEqual(len(posts), 3)
        self.assertTrue(all(
            post[1]["baseGenome"]
            is training_orchestrator.active_training_sessions[session_id]["population"]
            for post in posts
        ))
        started_calls = [
            call for call in self.db_calls
            if call[0] == "mark_training_batch_game_started"
        ]
        self.assertEqual(
            [call[1] for call in started_calls],
            [
                (session_id, "game-1", 1, 1),
                (session_id, "game-2", 1, 2),
                (session_id, "game-3", 1, 3),
            ],
        )

    async def test_duplicate_game_end_does_not_double_count_entries(self):
        class FakeResponse:
            status_code = 200
            text = "ok"

            def json(self):
                return {"entries": [{"game_id": "game-1", "fitness": 10, "genome": {"food_weight": 1.0}}]}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def get(self, *_args, **_kwargs):
                return FakeResponse()

        original_client = training_orchestrator.httpx.AsyncClient
        training_orchestrator.httpx.AsyncClient = FakeClient
        training_orchestrator.active_training_sessions["session-1"] = {
            "ruleset": "default",
            "bot_count": 2,
            "generations_left": 1,
            "population": [{"food_weight": 1.0}, {"food_weight": 0.0}],
            "generation": 1,
            "elite_count": 1,
            "selection_size": 1,
            "mutation_strength": 0.0,
            "mutation_rate": 0.0,
            "random_immigrant_count": 0,
            "generation_statistics": [],
            "bot_model": "GOAPGenetic",
            "games_per_generation": 1,
            "games_completed": 0,
            "games_failed": 0,
            "fitness_entries": [],
            "games": ["game-1"],
            "all_fitness_entries": [],
        }
        try:
            await training_orchestrator.handle_training_game_ended("game-1", "session-1")
            await training_orchestrator.handle_training_game_ended("game-1", "session-1")
        finally:
            training_orchestrator.httpx.AsyncClient = original_client

        complete_calls = [call for call in self.db_calls if call[0] == "complete_training_batch"]
        self.assertEqual(len(complete_calls), 1)

    async def test_successful_game_end_marks_attempt_completed_with_fitness_summary(self):
        class FakeResponse:
            status_code = 200
            text = "ok"

            def json(self):
                return {"entries": [
                    {"game_id": "game-1", "fitness": 10, "genome": {"food_weight": 1.0}},
                    {"game_id": "game-1", "fitness": 6, "genome": {"food_weight": 0.5}},
                ]}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def get(self, *_args, **_kwargs):
                return FakeResponse()

        original_client = training_orchestrator.httpx.AsyncClient
        training_orchestrator.httpx.AsyncClient = FakeClient
        training_orchestrator.active_training_sessions["session-1"] = {
            "ruleset": "default",
            "bot_count": 2,
            "generations_left": 1,
            "population": [{"food_weight": 1.0}, {"food_weight": 0.0}],
            "generation": 1,
            "elite_count": 1,
            "selection_size": 1,
            "mutation_strength": 0.0,
            "mutation_rate": 0.0,
            "random_immigrant_count": 0,
            "generation_statistics": [],
            "bot_model": "GOAPGenetic",
            "games_per_generation": 1,
            "games_completed": 0,
            "games_failed": 0,
            "fitness_entries": [],
            "games": ["game-1"],
            "all_fitness_entries": [],
        }
        try:
            await training_orchestrator.handle_training_game_ended("game-1", "session-1")
        finally:
            training_orchestrator.httpx.AsyncClient = original_client

        completed_calls = [
            call for call in self.db_calls
            if call[0] == "mark_training_batch_game_completed"
        ]
        self.assertEqual(len(completed_calls), 1)
        self.assertEqual(completed_calls[0][1][0:3], ("session-1", "game-1", 2))
        self.assertEqual(completed_calls[0][1][3]["best_fitness"], 10.0)
        self.assertEqual(completed_calls[0][1][3]["average_fitness"], 8.0)

    async def test_reconcile_stalled_training_sessions_marks_missing_stale_batch(self):
        class FakeDB:
            def __init__(self):
                self.status_updates = []

            def get_training_batches(self):
                return [{
                    "batch_id": "batch-1",
                    "status": "running",
                    "last_heartbeat_at": datetime.now() - timedelta(seconds=120),
                }]

            def update_training_batch_status(self, batch_id, status, error_message=None):
                self.status_updates.append((batch_id, status, error_message))

        fake_db = FakeDB()
        original_db = training_orchestrator.db
        training_orchestrator.db = fake_db
        training_orchestrator.active_training_sessions.clear()
        try:
            await training_orchestrator.reconcile_stalled_training_sessions(
                stale_after_seconds=30,
            )
        finally:
            training_orchestrator.db = original_db

        self.assertEqual(len(fake_db.status_updates), 1)
        self.assertEqual(fake_db.status_updates[0][0], "batch-1")
        self.assertEqual(fake_db.status_updates[0][1], "stalled")
        self.assertIn("not active", fake_db.status_updates[0][2])

    async def test_reconcile_stalled_training_sessions_marks_stale_active_attempt_failed(self):
        training_orchestrator.active_training_sessions["session-1"] = {
            "ruleset": "default",
            "bot_count": 2,
            "generations_left": 1,
            "population": [{"food_weight": 1.0}, {"food_weight": 0.0}],
            "generation": 1,
            "elite_count": 1,
            "selection_size": 1,
            "mutation_strength": 0.0,
            "mutation_rate": 0.0,
            "random_immigrant_count": 0,
            "generation_statistics": [],
            "bot_model": "GOAPGenetic",
            "games_per_generation": 1,
            "games_completed": 0,
            "games_failed": 0,
            "fitness_entries": [],
            "games": ["game-1"],
            "all_fitness_entries": [],
            "processed_game_ids": set(),
            "generation_terminal_game_ids": set(),
            "generation_lock": asyncio.Lock(),
            "generation_attempts": {
                "game-1": {
                    "attempt": 1,
                    "status": "running",
                    "updated_at": datetime.now() - timedelta(seconds=120),
                }
            },
        }

        await training_orchestrator.reconcile_stalled_training_sessions(
            stale_after_seconds=600,
            attempt_stale_after_seconds=30,
        )

        failed_calls = [
            call for call in self.db_calls
            if call[0] == "mark_training_batch_game_failed"
        ]
        self.assertEqual(len(failed_calls), 1)
        self.assertEqual(failed_calls[0][1][0:2], ("session-1", "game-1"))
        self.assertIn("stale", failed_calls[0][1][2])
        self.assertNotIn("session-1", training_orchestrator.active_training_sessions)

    async def test_cancel_training_session_marks_batch_cancelled_and_removes_active_session(self):
        training_orchestrator.active_training_sessions["session-1"] = {
            "generation_lock": asyncio.Lock(),
        }

        result = await training_orchestrator.cancel_training_session(
            "session-1", reason="operator requested cancel")

        status_calls = [
            call for call in self.db_calls
            if call[0] == "update_training_batch_status"
        ]
        self.assertTrue(result)
        self.assertNotIn("session-1", training_orchestrator.active_training_sessions)
        self.assertEqual(status_calls[0][1], (
            "session-1",
            "cancelled",
            "operator requested cancel",
        ))


if __name__ == "__main__":
    unittest.main()
