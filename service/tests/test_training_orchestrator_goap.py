import importlib
import os
import sys
import types
import unittest

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(SERVICE_DIR, ".."))
for path in (SERVICE_DIR, ROOT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

httpx_stub = types.ModuleType("httpx")
setattr(httpx_stub, "AsyncClient", object)
sys.modules["httpx"] = httpx_stub

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


class TrainingOrchestratorGOAPGenomeTests(unittest.TestCase):
    def test_goap_model_uses_goap_specific_fields(self):
        fields = training_genomes.get_genome_fields_for_model("GOAPGenetic")

        self.assertIn("warmth_desperation_weight", fields)
        self.assertIn("sickness_desperation_weight", fields)
        self.assertIn("trade_deception_weight", fields)
        self.assertIn("wage_deception_weight", fields)
        self.assertIn("resource_urgency_curve", fields)
        self.assertIn("action_cost_weight", fields)
        self.assertIn("tie_break_weight", fields)
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


if __name__ == "__main__":
    unittest.main()
