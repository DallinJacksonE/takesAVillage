import os
import sys
import types
import unittest

BOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BOTS_DIR, ".."))
for path in (BOTS_DIR, ROOT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

httpx_stub = types.ModuleType("httpx")
setattr(httpx_stub, "AsyncClient", object)
websockets_stub = types.ModuleType("websockets")
setattr(websockets_stub, "connect", None)
sys.modules.setdefault("httpx", httpx_stub)
sys.modules.setdefault("websockets", websockets_stub)

from models.goap_genetic.GOAPGenetic import GOAPGenetic
from models.goap_genetic.action_generator import ActionGenerator
from models.goap_genetic.action_features import ActionFeatureCalculator, ActionUtilityScorer
from models.goap_genetic.acting import Actuator
from models.goap_genetic.domain import Command
from models.goap_genetic.goals import GoalLibrary, GOAPGoal
from models.goap_genetic.goap_actions import ActionTemplate, OneStepPlanner, PlannedAction
from models.goap_genetic.goap_genome import GOAPGenome
from models.goap_genetic.memory import DecisionContext, Memory
from models.goap_genetic.perception import Perception
from models.goap_genetic.thinking import Thinker
from bot_multiprocessing import ActionSubmissionGate, create_genome_for_model, seed_genomes_for_model


class GOAPGenomeTests(unittest.TestCase):
    def test_random_goap_genome_uses_minus_one_to_one_gene_range(self):
        genome = GOAPGenome.random()

        self.assertTrue(genome.__dict__)
        for gene_name, gene_value in genome.__dict__.items():
            self.assertGreaterEqual(gene_value, -1.0, gene_name)
            self.assertLessEqual(gene_value, 1.0, gene_name)

    def test_phase_four_preference_genes_are_available_with_neutral_defaults(self):
        genome = GOAPGenome()

        for gene_name in [
            "resource_urgency_curve",
            "survival_urgency_weight",
            "health_risk_weight",
            "maintenance_urgency_weight",
            "production_discount_weight",
            "trade_fairness_weight",
            "employment_wage_weight",
            "employer_exploitation_weight",
            "campfire_accept_weight",
            "finalize_honesty_weight",
            "tie_break_weight",
            "action_cost_weight",
        ]:
            self.assertTrue(hasattr(genome, gene_name), gene_name)
            self.assertEqual(getattr(genome, gene_name), 0.0, gene_name)

    def test_gene_multiplier_transforms_stay_bounded_and_neutral(self):
        self.assertEqual(GOAPGenome.positive_multiplier(0.0), 1.0)
        self.assertEqual(GOAPGenome.positive_multiplier(-1.0), 0.0)
        self.assertEqual(GOAPGenome.positive_multiplier(1.0), 2.0)

    def test_from_dict_accepts_legacy_genome_fields_and_fills_goap_specific_fields(self):
        genome = GOAPGenome.from_dict({
            "food_weight": 0.75,
            "wood_weight": -0.25,
            "unknown_future_field": 99,
        })

        self.assertEqual(genome.food_weight, 0.75)
        self.assertEqual(genome.wood_weight, -0.25)
        self.assertTrue(hasattr(genome, "warmth_desperation_weight"))
        self.assertTrue(hasattr(genome, "sickness_desperation_weight"))

    def test_goap_genetic_from_json_uses_goap_genome_without_touching_genetic_bot_genome(self):
        bot = GOAPGenetic.from_json({"food_weight": 0.5})

        self.assertIsInstance(bot.genome, GOAPGenome)
        self.assertEqual(bot.genome.food_weight, 0.5)


class GOAPPerceptionTests(unittest.TestCase):
    def test_perception_includes_agent_context_needed_for_planning(self):
        memory = Perception().sense({
            "day": 3,
            "game_length": 15,
            "time_remaining": 42,
            "phase": "WORK",
            "development_costs": {"Farm": {"build": {"wood": 2}}},
            "campfire_cost": {"wood": 1},
            "max_fire_seats": 3,
            "player_list": [{"id": "bot-1", "health": "healthy"}],
            "map": {"tile-1": {"id": "tile-1", "type": "Farm"}},
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 1, "wood": 2, "iron": 0},
                "actions": [],
                "available_work": [],
                "fire_status": "COLD",
                "fire_guests": [],
                "finished_phase": False,
            },
            "developments": [],
        })

        self.assertIsInstance(memory, Memory)
        self.assertEqual(memory["day"], 3)
        self.assertEqual(memory["game_length"], 15)
        self.assertEqual(memory["time_remaining"], 42)
        self.assertEqual(memory["my_id"], "bot-1")
        self.assertEqual(memory["development_costs"], {"Farm": {"build": {"wood": 2}}})
        self.assertEqual(memory["campfire_cost"], {"wood": 1})
        self.assertEqual(memory["max_fire_seats"], 3)
        self.assertEqual(memory["players"][0]["id"], "bot-1")
        self.assertEqual(memory["map"]["tile-1"]["type"], "Farm")
        self.assertFalse(memory["finished_phase"])

    def test_perception_computes_only_objective_derived_features(self):
        memory = Perception().sense({
            "phase": "WORK",
            "development_costs": {
                "Farm": {"build": {"wood": 2}},
                "Woods": {"build": {"wood": 10}},
            },
            "map": {
                "farm-tile": {"id": "farm-tile", "type": "Farm", "development": None},
                "woods-tile": {"id": "woods-tile", "type": "Woods", "development": None},
            },
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 1, "wood": 2, "iron": 0},
                "actions": [
                    {"id": "trade-1", "type": "TRADE", "status": "PENDING", "waiting_on_id": "bot-1"},
                ],
                "available_work": [],
            },
            "developments": [
                {"id": "mine-1", "type": "Mine", "owner_id": "bot-2", "is_contested": True},
            ],
        })

        self.assertEqual(memory["resource_total"], 3)
        self.assertEqual([tile["id"] for tile in memory["affordable_build_tiles"]], ["farm-tile"])
        self.assertEqual(memory["resource_production_by_dev"]["mine-1"], "iron")
        self.assertEqual(memory["candidate_trade_inventory"], {"food": 1, "wood": 2, "iron": 0})
        self.assertEqual(memory["contested_developments"][0]["id"], "mine-1")
        self.assertNotIn("urgency", memory)


    def test_perception_handles_representative_work_trade_and_night_states(self):
        base_me = {
            "id": "bot-1",
            "health": "healthy",
            "resources": {"food": 1, "wood": 2, "iron": 0},
            "actions": [],
            "available_work": [],
            "fire_status": "COLD",
            "fire_guests": [],
        }
        work = Perception().sense({
            "phase": "WORK",
            "me": {**base_me, "available_work": [{"id": "job-1"}]},
            "developments": [
                {"id": "dev-1", "type": "Farm", "owner_id": "bot-1", "is_contested": False},
            ],
        })
        trade = Perception().sense({
            "phase": "TRADE",
            "me": {**base_me, "actions": [
                {"id": "trade-1", "type": "TRADE", "status": "PENDING", "waiting_on_id": "bot-1"},
            ]},
            "developments": [],
        })
        night = Perception().sense({
            "phase": "NIGHT",
            "campfire_cost": {"wood": 1},
            "max_fire_seats": 2,
            "me": base_me,
            "developments": [],
        })

        self.assertEqual(work["phase"], "WORK")
        self.assertEqual(work["available_work"][0]["id"], "job-1")
        self.assertEqual(work["my_developments"][0]["id"], "dev-1")
        self.assertEqual(trade["phase"], "TRADE")
        self.assertEqual(trade["pending_contracts"][0]["id"], "trade-1")
        self.assertEqual(trade["candidate_trade_inventory"], {"food": 1, "wood": 2, "iron": 0})
        self.assertEqual(night["phase"], "NIGHT")
        self.assertEqual(night["campfire_cost"], {"wood": 1})
        self.assertEqual(night["max_fire_seats"], 2)


class GOAPPlannerTests(unittest.TestCase):
    def test_goal_library_exposes_explicit_desired_state_goals(self):
        goals = GoalLibrary(GOAPGenome()).all_goals()
        names = {goal.name for goal in goals}

        self.assertIn("SURVIVE", names)
        self.assertIn("SECURE_FOOD", names)
        self.assertIn("SECURE_WARMTH", names)
        self.assertIn("INCREASE_PRODUCTION", names)
        self.assertTrue(all(isinstance(goal, GOAPGoal) for goal in goals))
        self.assertTrue(all(goal.desired_state for goal in goals))
        self.assertTrue(all(callable(goal.utility) for goal in goals))
        self.assertTrue(all(callable(goal.is_complete) for goal in goals))

    def test_action_template_binds_only_matching_legal_server_actions(self):
        template = ActionTemplate(
            name="build-development",
            command=Command.BUILD_DEV,
            effects={"production_capacity": 1},
            cost=lambda _memory, _action: 0.0,
        )
        legal_actions = [
            {"action_command": Command.EMPLOYMENT, "payload": {"wage_type": "food", "wage": 1}},
            {"action_command": Command.BUILD_DEV, "payload": {"tile_id": "farm", "_tile_type": "Farm"}},
        ]

        planned = template.bind(legal_actions, Memory({}))

        self.assertEqual(len(planned), 1)
        self.assertIsInstance(planned[0], PlannedAction)
        self.assertEqual(planned[0].server_action["action_command"], Command.BUILD_DEV)
        self.assertEqual(planned[0].effects, {"production_capacity": 1})

    def test_all_action_templates_bind_reject_and_emit_legal_payloads(self):
        bot = GOAPGenetic(GOAPGenome())
        planner = OneStepPlanner(bot.genome)
        memory = Memory({
            "food": 1,
            "wood": 2,
            "iron": 0,
            "fire_status": "COLD",
            "sickness_chance": 0.0,
            "campfire_cost": {"wood": 1},
            "development_costs": {"Farm": {"build": {"wood": 2}}},
            "my_developments": [{"id": "dev-1", "upgrade_cost": {"wood": 1}, "maintenance_cost": {"food": 1}}],
            "other_player_developments": [{"id": "dev-2"}],
            "pending_contracts": [{"id": "trade-1"}],
        })
        legal_by_command = {
            Command.START_FIRE: {"action_command": Command.START_FIRE, "payload": {}},
            Command.CAMPFIRE: {"action_command": Command.CAMPFIRE, "payload": {"target_id": "bot-2", "is_request": True}},
            Command.EMPLOYMENT: {"action_command": Command.EMPLOYMENT, "payload": {"wage_type": "food", "wage": 1}},
            Command.COMMIT_WORK: {"action_command": Command.COMMIT_WORK, "payload": {"job": {"wage_type": "wood", "wage": 1}}},
            Command.BUILD_DEV: {"action_command": Command.BUILD_DEV, "payload": {"tile_id": "tile-1", "_tile_type": "Farm"}},
            Command.MAINTAIN_DEV: {"action_command": Command.MAINTAIN_DEV, "payload": {"dev_id": "dev-1"}},
            Command.UPGRADE_DEV: {"action_command": Command.UPGRADE_DEV, "payload": {"dev_id": "dev-1"}},
            Command.CONTEST_DEV: {"action_command": Command.CONTEST_DEV, "payload": {"dev_id": "dev-2", "side": "INITIATOR"}},
            Command.TRADE: {"action_command": Command.TRADE, "payload": {"target_id": "bot-2", "offer_items": {"wood": 1}, "request_items": {"food": 1}}},
            Command.ACCEPT: {"action_command": Command.ACCEPT, "payload": {"action_id": "contract-1"}},
            Command.FINALIZE: {"action_command": Command.FINALIZE, "payload": {"action_id": "contract-1", "actual_items": {"wood": 1}}},
        }
        command_vocabulary = {value for name, value in vars(Command).items() if name.isupper()}

        for template in planner.templates:
            with self.subTest(template=template.name):
                action = legal_by_command[template.command]
                bound = template.bind([action, {"action_command": Command.FINISH_PHASE, "payload": {}}], memory)

                self.assertEqual(len(bound), 1)
                self.assertIn(bound[0].server_action["action_command"], command_vocabulary)
                self.assertIsInstance(bound[0].effects, dict)
                self.assertIsInstance(bound[0].cost, float)
                self.assertEqual(template.bind([{"action_command": "WRONG", "payload": {}}], memory), [])
                self.assertFalse(any(
                    key.startswith("_")
                    for key in bot.format_network_payload(bound[0].server_action)["payload"]
                ))

    def test_basebot_available_actions_use_goap_command_vocabulary(self):
        bot = GOAPGenetic(GOAPGenome())
        command_vocabulary = {value for name, value in vars(Command).items() if name.isupper()}
        state = {
            "status": "RUNNING",
            "phase": "WORK",
            "development_costs": {"Farm": {"build": {"wood": 1}}},
            "map": {"tile-1": {"id": "tile-1", "type": "Farm", "development": None}},
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 2, "wood": 2, "iron": 1},
                "actions": [],
                "available_work": [],
            },
            "player_list": [{"id": "bot-1", "health": "healthy"}],
            "developments": [],
        }

        actions = bot.get_available_actions(state)

        self.assertTrue(actions)
        self.assertTrue({action["action_command"] for action in actions}.issubset(command_vocabulary))

    def test_one_step_planner_scores_effect_progress_and_cost(self):
        genome = GOAPGenome(food_desperation_weight=1.0, wood_desperation_weight=-1.0)
        planner = OneStepPlanner(genome)
        goal = GoalLibrary(genome).by_name("SECURE_FOOD")
        memory = Memory({"food": 0, "wood": 8, "iron": 1, "fire_status": "HOST", "sickness_chance": 0.0})
        legal_actions = [
            {"action_command": Command.EMPLOYMENT, "payload": {"wage_type": "wood", "wage": 3}},
            {"action_command": Command.EMPLOYMENT, "payload": {"wage_type": "food", "wage": 1}},
        ]

        planned = planner.plan(goal, legal_actions, memory)

        self.assertIsNotNone(planned)
        self.assertEqual(planned.server_action["payload"]["wage_type"], "food")
        self.assertGreater(planned.score, 0)

    def test_resource_urgency_curve_gene_controls_goal_utility_shape(self):
        low_food = Memory({"food": 0, "wood": 2, "iron": 0, "fire_status": "HOST", "sickness_chance": 0.0})
        high_food = Memory({"food": 8, "wood": 2, "iron": 0, "fire_status": "HOST", "sickness_chance": 0.0})
        flat_goal = GoalLibrary(GOAPGenome(
            food_desperation_weight=1.0,
            resource_urgency_curve=-1.0,
        )).by_name("SECURE_FOOD")
        curved_goal = GoalLibrary(GOAPGenome(
            food_desperation_weight=1.0,
            resource_urgency_curve=1.0,
        )).by_name("SECURE_FOOD")

        self.assertEqual(flat_goal.utility(low_food), flat_goal.utility(high_food))
        self.assertGreater(curved_goal.utility(low_food), curved_goal.utility(high_food))

    def test_action_cost_weight_controls_resource_cost_penalty(self):
        goal = GoalLibrary(GOAPGenome(growth_weight=1.0, build_weight=1.0)).by_name("INCREASE_PRODUCTION")
        memory = Memory({
            "food": 2,
            "wood": 2,
            "iron": 0,
            "development_costs": {"Farm": {"build": {"wood": 2}}},
        })
        legal_actions = [
            {"action_command": Command.BUILD_DEV, "payload": {"tile_id": "farm", "_tile_type": "Farm"}},
        ]
        free_planner = OneStepPlanner(GOAPGenome(growth_weight=1.0, build_weight=1.0, action_cost_weight=0.0, wood_weight=1.0))
        costly_planner = OneStepPlanner(GOAPGenome(growth_weight=1.0, build_weight=1.0, action_cost_weight=1.0, wood_weight=1.0))

        free_plan = free_planner.plan(goal, legal_actions, memory)
        costly_plan = costly_planner.plan(goal, legal_actions, memory)

        self.assertGreater(free_plan.score, costly_plan.score)

    def test_action_features_are_factual_and_normalized_for_work_and_build(self):
        calculator = ActionFeatureCalculator()
        memory = Memory({
            "day": 3,
            "game_length": 13,
            "food": 0,
            "wood": 6,
            "iron": 1,
            "development_costs": {"Farm": {"build": {"wood": 2}}},
        })

        employment = calculator.calculate(
            {"action_command": Command.EMPLOYMENT, "payload": {"wage_type": "food", "wage": 3}},
            memory,
        )
        build = calculator.calculate(
            {"action_command": Command.BUILD_DEV, "payload": {"tile_id": "farm", "_tile_type": "Farm"}},
            memory,
        )

        self.assertEqual(employment["food_delta"], 3.0)
        self.assertEqual(employment["resource_delta"], 3.0)
        self.assertEqual(build["resource_cost"], 2.0)
        self.assertAlmostEqual(build["production_delta"], 10 / 13)
        for feature_value in build.values():
            self.assertGreaterEqual(feature_value, -1.0)
            self.assertLessEqual(feature_value, 3.0)

    def test_action_feature_scorer_is_genome_weighted_dot_product(self):
        features = {"food_delta": 2.0, "wood_delta": 1.0, "resource_cost": 1.0}
        food_genome = GOAPGenome(food_weight=1.0, wood_weight=0.0, action_cost_weight=0.0)
        wood_genome = GOAPGenome(food_weight=0.0, wood_weight=1.0, action_cost_weight=0.0)

        food_eval = ActionUtilityScorer(food_genome).score(features)
        wood_eval = ActionUtilityScorer(wood_genome).score(features)

        self.assertGreater(food_eval.score, wood_eval.score)
        self.assertEqual(food_eval.contributions["food_delta"], 2.0)
        self.assertIn("food_delta", food_eval.top_features())

    def test_planned_action_carries_debug_explanation_for_chosen_features(self):
        genome = GOAPGenome(
            food_weight=1.0,
            food_desperation_weight=1.0,
            work_weight=1.0,
        )
        planner = OneStepPlanner(genome)
        goal = GoalLibrary(genome).by_name("SECURE_FOOD")
        memory = Memory({"food": 0, "wood": 2, "iron": 0, "fire_status": "HOST", "sickness_chance": 0.0})

        planned = planner.plan(goal, [
            {"action_command": Command.EMPLOYMENT, "payload": {"wage_type": "food", "wage": 1}},
        ], memory)

        self.assertIsNotNone(planned)
        self.assertIn("features", planned.explanation)
        self.assertIn("weights", planned.explanation)
        self.assertIn("top_features", planned.explanation)
        self.assertIn("food_delta", planned.explanation["top_features"])

    def test_actuator_replans_from_current_legal_actions_each_call(self):
        actuator = Actuator(GOAPGenome(food_desperation_weight=1.0, fire_weight=1.0))
        memory = Memory({"food": 0, "wood": 1, "iron": 0, "fire_status": "COLD", "sickness_chance": 0.0})

        first = actuator.act("SURVIVE", [{"action_command": Command.START_FIRE, "payload": {}}], memory)
        second = actuator.act("SURVIVE", [{"action_command": Command.EMPLOYMENT, "payload": {"wage_type": "food", "wage": 1}}], memory)

        self.assertEqual(first["action_command"], Command.START_FIRE)
        self.assertEqual(second["action_command"], Command.EMPLOYMENT)


class GOAPActionGeneratorTests(unittest.TestCase):
    def test_start_fire_is_host_fire_and_campfire_is_social_invite_or_request(self):
        generator = ActionGenerator(GOAPGenome())
        actions = [
            {"action_command": Command.CAMPFIRE, "payload": {"target_id": "host", "is_request": True}},
            {"action_command": Command.START_FIRE, "payload": {}},
        ]
        memory = {"food": 2, "wood": 2, "iron": 0, "fire_status": "COLD"}

        action = generator.get_survival_action(actions, memory)

        self.assertEqual(action["action_command"], Command.START_FIRE)
        self.assertNotIn("is_request", action["payload"])

    def test_network_payload_strips_helper_keys_from_goap_action(self):
        bot = GOAPGenetic(GOAPGenome())
        action = bot.format_network_payload({
            "action_command": Command.BUILD_DEV,
            "payload": {"tile_id": "tile-1", "_tile_type": "Farm"},
        })

        self.assertEqual(action, {
            "action_command": Command.BUILD_DEV,
            "payload": {"tile_id": "tile-1"},
        })

    def test_goap_bot_waits_after_finishing_phase(self):
        bot = GOAPGenetic(GOAPGenome(survival_weight=1.0, fire_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "NIGHT",
            "campfire_cost": {"wood": 1},
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "finished_phase": True,
                "fire_status": "COLD",
                "resources": {"food": 2, "wood": 2, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy", "fire_status": "COLD"},
            ],
        }

        self.assertIsNone(bot.choose_action(state))

    def test_survival_action_uses_start_fire_command_for_night_warmth(self):
        generator = ActionGenerator(GOAPGenome(survival_weight=1.0, fire_weight=1.0))
        actions = [
            {"action_command": "EMPLOYMENT", "payload": {"wage_type": "food", "wage": 1}},
            {"action_command": "START_FIRE", "payload": {}},
        ]
        memory = {
            "phase": "NIGHT",
            "fire_status": "COLD",
            "sickness_chance": 0.2,
            "food": 2,
            "wood": 1,
            "iron": 0,
        }

        action = generator.get_survival_action(actions, memory)

        self.assertEqual(action["action_command"], "START_FIRE")

    def test_expansion_action_uses_build_dev_command(self):
        generator = ActionGenerator(GOAPGenome(build_weight=1.0, growth_weight=1.0))
        actions = [
            {"action_command": "BUILD_DEV", "payload": {"tile_id": "tile-1", "_tile_type": "Farm"}},
            {"action_command": "EMPLOYMENT", "payload": {"wage_type": "food", "wage": 1}},
        ]
        memory = {"food": 4, "wood": 4, "iron": 1}

        action = generator.get_expansion_action(actions, memory)

        self.assertEqual(action["action_command"], "BUILD_DEV")

    def test_expansion_build_prefers_farm_when_food_is_scarce(self):
        generator = ActionGenerator(GOAPGenome(
            build_weight=0.0,
            farm_preference=0.0,
            woods_preference=0.0,
            food_desperation_weight=1.0,
            wood_desperation_weight=-1.0,
        ))
        actions = [
            {"action_command": "BUILD_DEV", "payload": {"tile_id": "woods-tile", "_tile_type": "Woods"}},
            {"action_command": "BUILD_DEV", "payload": {"tile_id": "farm-tile", "_tile_type": "Farm"}},
        ]
        memory = {"food": 0, "wood": 8, "iron": 1}

        action = generator.get_expansion_action(actions, memory)

        self.assertEqual(action["payload"]["tile_id"], "farm-tile")

    def test_survival_employment_prefers_food_when_food_is_scarce(self):
        generator = ActionGenerator(GOAPGenome(
            food_desperation_weight=1.0,
            wood_desperation_weight=-1.0,
            work_weight=0.0,
        ))
        actions = [
            {"action_command": "EMPLOYMENT", "payload": {"wage_type": "wood", "wage": 3}},
            {"action_command": "EMPLOYMENT", "payload": {"wage_type": "food", "wage": 1}},
        ]
        memory = {"food": 0, "wood": 8, "iron": 1}

        action = generator.get_survival_action(actions, memory)

        self.assertEqual(action["payload"]["wage_type"], "food")


class GOAPThinkerTests(unittest.TestCase):
    def test_survival_score_increases_when_cold_and_warmth_gene_is_positive(self):
        thinker = Thinker(GOAPGenome(
            survival_weight=1.0,
            warmth_desperation_weight=1.0,
        ))
        warm_memory = {
            "food": 5,
            "wood": 5,
            "iron": 5,
            "sickness_chance": 0.0,
            "fire_status": "GUEST",
        }
        cold_memory = dict(warm_memory, fire_status="COLD")

        self.assertGreater(
            thinker._score_survival(cold_memory),
            thinker._score_survival(warm_memory),
        )


class GOAPActuatorTests(unittest.TestCase):
    def test_decision_context_pairs_typed_memory_with_legal_actions(self):
        memory = Memory({"phase": "WORK", "food": 1, "wood": 2, "iron": 0})
        actions = [{"action_command": Command.EMPLOYMENT, "payload": {}}]

        context = DecisionContext(memory=memory, legal_actions=actions)

        self.assertIs(context.memory, memory)
        self.assertEqual(context.legal_actions, actions)

    def test_fallback_tries_other_goal_actions_before_income(self):
        actuator = Actuator(GOAPGenome(survival_weight=1.0, fire_weight=1.0))
        actions = [
            {"action_command": "START_FIRE", "payload": {}},
            {"action_command": "EMPLOYMENT", "payload": {"wage_type": "food", "wage": 1}},
        ]
        memory = {
            "phase": "NIGHT",
            "fire_status": "COLD",
            "food": 2,
            "wood": 1,
            "iron": 0,
            "sickness_chance": 0.0,
        }

        action = actuator.act("EXPAND_TERRITORY", actions, memory)

        self.assertEqual(action["action_command"], "START_FIRE")


class BotServerGOAPGenomeTests(unittest.TestCase):

    def test_action_submission_gate_suppresses_duplicate_actions_for_unchanged_state(self):
        gate = ActionSubmissionGate()
        state = {
            "day": 1,
            "phase": "WORK",
            "status": "RUNNING",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "finished_phase": False,
                "resources": {"food": 1, "wood": 1, "iron": 0},
                "actions": [],
            },
        }
        action = {"action_command": Command.FINISH_PHASE, "payload": {}}

        self.assertTrue(gate.should_submit(state, action))
        self.assertFalse(gate.should_submit(state, action))
        self.assertTrue(gate.should_submit({**state, "day": 2}, action))

    def test_bot_server_creates_goap_genome_for_goap_model(self):
        genome = create_genome_for_model("GOAPGenetic", {"food_weight": -0.5})

        self.assertIsInstance(genome, GOAPGenome)
        self.assertEqual(genome.food_weight, -0.5)

    def test_bot_server_seeds_goap_population_with_goap_genomes(self):
        genomes = seed_genomes_for_model("GOAPGenetic", None, 3)

        self.assertEqual(len(genomes), 3)
        self.assertTrue(all(isinstance(genome, GOAPGenome) for genome in genomes))


if __name__ == "__main__":
    unittest.main()
