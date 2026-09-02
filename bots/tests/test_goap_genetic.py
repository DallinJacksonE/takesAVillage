import os
import sys
import unittest

BOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BOTS_DIR, ".."))
for path in (BOTS_DIR, ROOT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from models.goap_genetic.GOAPGenetic import GOAPGenetic
from models.goap_genetic.action_generator import ActionGenerator
from models.goap_genetic.action_features import ActionFeatureCalculator, ActionUtilityScorer
from models.goap_genetic.acting import Actuator
from models.goap_genetic.domain import Command
from models.goap_genetic.goals import GoalLibrary, GOAPGoal
from models.goap_genetic.goap_actions import ActionTemplate, OneStepPlanner, PlannedAction
from models.goap_genetic.goap_genome import GOAPGenome
from models.goap_genetic.planning.development_economics import DevelopmentEconomist
from models.goap_genetic.planning.partner_care import PartnerCareAnalyzer
from models.goap_genetic.planning.partner_specialization import PartnerSpecialistAnalyzer
from models.goap_genetic.planning.resource_valuation import ResourceValuator
from models.goap_genetic.planning.time_pressure import TimePressurePolicy
from models.goap_genetic.memory import DecisionContext, Memory
from models.goap_genetic.perception import Perception
from models.goap_genetic.social_memory import ExchangeClassifier, SocialMemory
from models.goap_genetic.thinking import Thinker
from models.utility_genetic.GeneticBot import GeneticBot
from models.utility_genetic.Genome import Genome
from bot_multiprocessing import ActionSubmissionGate, create_genome_for_model, seed_genomes_for_model


class GOAPGenomeTests(unittest.TestCase):
    def test_random_goap_genome_uses_nonnegative_survival_core_fields(self):
        genome = GOAPGenome.random()

        self.assertTrue(genome.__dict__)
        for gene_name, gene_value in genome.__dict__.items():
            self.assertGreaterEqual(gene_value, -1.0, gene_name)
            self.assertLessEqual(gene_value, 1.0, gene_name)
        for gene_name in GOAPGenome.nonnegative_field_names():
            self.assertGreaterEqual(getattr(genome, gene_name), 0.0, gene_name)

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
        self.assertEqual(genome.wood_weight, 0.0)
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

    def test_perception_derives_development_economy_facts(self):
        memory = Perception().sense({
            "phase": "WORK",
            "day": 2,
            "game_length": 8,
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 1, "wood": 0, "iron": 0},
                "actions": [],
                "available_work": [
                    {"development": {"id": "farm-1", "owner_id": "bot-1"}, "wage": 2, "wage_type": "food"},
                ],
            },
            "developments": [
                {
                    "id": "farm-1",
                    "type": "Farm",
                    "level": 2,
                    "owner_id": "bot-1",
                    "maintenance_days": 1,
                    "maintenance_cost": {"wood": 2, "iron": 1},
                    "upgrade_cost": {"wood": 3, "iron": 1},
                    "can_upgrade": True,
                },
            ],
        })

        self.assertEqual(memory["owned_production_by_resource"], {"food": 2.0})
        self.assertEqual(memory["maintenance_resource_deficits"], {"wood": 2.0, "iron": 1.0})
        self.assertEqual(memory["upgrade_resource_deficits"], {"wood": 3.0, "iron": 1.0})
        self.assertEqual(memory["at_risk_developments"][0]["id"], "farm-1")
        self.assertEqual(memory["upgradable_developments"][0]["id"], "farm-1")
        self.assertEqual(memory["workable_owned_developments"][0]["id"], "farm-1")
        self.assertGreater(memory["upgrade_opportunity_value_by_resource"]["food"], 0.0)


class GOAPDevelopmentEconomyTests(unittest.TestCase):
    def test_development_output_scales_with_level_per_laborer(self):
        economist = DevelopmentEconomist()

        self.assertEqual(economist.production_per_labor({"type": "Farm", "level": 2}), 2.0)
        self.assertEqual(economist.production_per_labor({"type": "Farm", "level": 3}), 3.0)

    def test_upgrade_marginal_output_is_one_extra_resource_per_laborer_per_remaining_day(self):
        economist = DevelopmentEconomist()
        dev = {"id": "farm-1", "type": "Farm", "level": 2, "owner_id": "bot-1"}
        memory = Memory({
            "my_id": "bot-1",
            "day": 2,
            "game_length": 6,
            "available_work": [
                {"development": {"id": "farm-1", "owner_id": "bot-1"}},
            ],
            "pending_contracts": [
                {"type": "EMPLOYMENT", "status": "ACCEPTED", "dev_id": "farm-1", "initiator_id": "bot-2", "target_id": "bot-1"},
            ],
        })

        self.assertEqual(economist.expected_laborers(dev, memory), 2.0)
        self.assertEqual(economist.upgrade_marginal_output(dev, memory), {"food": 8.0})

    def test_development_economist_computes_risk_and_future_resource_deficits(self):
        economist = DevelopmentEconomist()
        memory = Memory({
            "food": 1,
            "wood": 0,
            "iron": 1,
            "my_developments": [
                {
                    "id": "woods-1",
                    "type": "Woods",
                    "level": 2,
                    "owner_id": "bot-1",
                    "maintenance_days": 1,
                    "maintenance_cost": {"food": 2, "iron": 1},
                    "upgrade_cost": {"food": 3, "iron": 2},
                    "can_upgrade": True,
                },
            ],
        })

        self.assertGreater(economist.maintenance_loss_risk(memory["my_developments"][0], memory), 0.9)
        self.assertEqual(economist.maintenance_required_resources(memory), {"food": 1.0})
        self.assertEqual(economist.upgrade_required_resources(memory), {"food": 2.0, "iron": 1.0})


class GOAPPartnerSpecializationTests(unittest.TestCase):
    def test_partner_analyzer_scores_trusted_complementary_specialists(self):
        analyzer = PartnerSpecialistAnalyzer()
        memory = Memory({
            "my_id": "bot-1",
            "food": 0,
            "wood": 5,
            "iron": 0,
            "maintenance_resource_deficits": {"iron": 1.0},
            "upgrade_resource_deficits": {"iron": 1.0},
            "other_player_developments": [
                {"id": "mine-1", "type": "Mine", "level": 3, "owner_id": "bot-2"},
                {"id": "farm-1", "type": "Farm", "level": 2, "owner_id": "bot-3"},
            ],
            "relationships": {
                "bot-2": {"trust": 0.8, "fairness": 0.5, "generosity": 0.2, "reciprocity": 0.3, "hostility": 0.0, "confidence": 0.75},
                "bot-3": {"trust": -0.4, "fairness": 0.0, "generosity": 0.0, "reciprocity": 0.0, "hostility": 0.5, "confidence": 0.75},
            },
        })

        facts = analyzer.analyze(memory)

        self.assertEqual(facts["partner_production_by_resource"]["bot-2"], {"iron": 3.0})
        self.assertEqual(facts["partner_specializations"]["bot-2"], "iron")
        self.assertGreater(facts["complementary_partner_scores"]["bot-2"], facts["complementary_partner_scores"].get("bot-3", 0.0))
        self.assertGreater(facts["trusted_partner_scores"]["bot-2"], facts["trusted_partner_scores"]["bot-3"])

    def test_perception_adds_partner_specialization_facts_to_memory(self):
        memory = Perception().sense({
            "phase": "WORK",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 0, "wood": 4, "iron": 0},
                "actions": [],
                "available_work": [],
            },
            "developments": [
                {"id": "mine-1", "type": "Mine", "level": 2, "owner_id": "bot-2"},
            ],
        })

        self.assertEqual(memory["partner_production_by_resource"]["bot-2"], {"iron": 2.0})
        self.assertEqual(memory["partner_specializations"]["bot-2"], "iron")

    def test_partner_care_analyzer_identifies_trusted_sick_partner_needing_food(self):
        analyzer = PartnerCareAnalyzer()
        memory = Memory({
            "my_id": "bot-1",
            "food": 3,
            "wood": 2,
            "fire_status": "HOST",
            "players": [
                {"id": "bot-1", "health": "healthy", "resources": {"food": 3}, "fire_status": "HOST"},
                {"id": "trusted-farmer", "health": "sick", "resources": {"food": 0}, "fire_status": "HOST"},
            ],
            "trusted_partner_scores": {"trusted-farmer": 0.8},
            "complementary_partner_scores": {"trusted-farmer": 1.0},
            "relationships": {"trusted-farmer": {"hostility": 0.0, "confidence": 0.8}},
        })

        facts = analyzer.analyze(memory)

        self.assertIn("trusted-farmer", facts["free_food_support_targets"])
        self.assertGreater(facts["partner_care_needs"]["trusted-farmer"]["food"], 0.0)
        self.assertIn("trusted-farmer", facts["trusted_sick_partners"])

    def test_partner_care_analyzer_identifies_trusted_cold_partner_needing_fire(self):
        analyzer = PartnerCareAnalyzer()
        memory = Memory({
            "my_id": "bot-1",
            "fire_status": "HOST",
            "fire_guests": [],
            "max_fire_seats": 2,
            "players": [
                {"id": "bot-1", "health": "healthy", "fire_status": "HOST"},
                {"id": "trusted-miner", "health": "sick", "fire_status": "COLD", "resources": {"food": 1}},
            ],
            "trusted_partner_scores": {"trusted-miner": 0.6},
            "complementary_partner_scores": {"trusted-miner": 2.0},
        })

        facts = analyzer.analyze(memory)

        self.assertIn("trusted-miner", facts["campfire_support_targets"])
        self.assertGreater(facts["partner_care_needs"]["trusted-miner"]["campfire"], 0.0)

    def test_partner_care_analyzer_ignores_hostile_partner_for_free_support(self):
        analyzer = PartnerCareAnalyzer()
        memory = Memory({
            "my_id": "bot-1",
            "food": 4,
            "players": [
                {"id": "bot-1", "health": "healthy", "resources": {"food": 4}},
                {"id": "hostile-miner", "health": "sick", "resources": {"food": 0}, "fire_status": "COLD"},
            ],
            "trusted_partner_scores": {"hostile-miner": -0.5},
            "complementary_partner_scores": {"hostile-miner": 2.0},
            "relationships": {"hostile-miner": {"hostility": 0.9, "confidence": 1.0}},
        })

        facts = analyzer.analyze(memory)

        self.assertNotIn("hostile-miner", facts["free_food_support_targets"])
        self.assertNotIn("hostile-miner", facts["campfire_support_targets"])

    def test_perception_adds_partner_care_facts_to_memory(self):
        memory = Perception().sense({
            "phase": "NIGHT",
            "max_fire_seats": 2,
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "HOST",
                "fire_guests": [],
                "resources": {"food": 3, "wood": 2, "iron": 0},
                "actions": [],
                "available_work": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy", "fire_status": "HOST", "resources": {"food": 3}},
                {"id": "bot-2", "health": "sick", "fire_status": "COLD", "resources": {"food": 0}},
            ],
            "developments": [
                {"id": "mine-1", "type": "Mine", "level": 2, "owner_id": "bot-2"},
            ],
        })

        self.assertIn("free_food_support_targets", memory)
        self.assertIn("campfire_support_targets", memory)
        self.assertIn("partner_care_needs", memory)


class GOAPSocialMemoryTests(unittest.TestCase):
    def test_social_memory_classifies_free_food_support_as_generous(self):
        evidence = ExchangeClassifier().classify({
            "id": "support-1",
            "counterparty_id": "helper",
            "reason": "SICK_PARTNER_FOOD",
            "actual_received": {"food": 1},
            "actual_sent": {},
        })

        self.assertEqual(evidence.kind, "support_received")
        self.assertGreater(evidence.trust, 0.0)
        self.assertGreater(evidence.generosity, 0.0)
        self.assertGreater(evidence.affinity, 0.0)

    def test_social_memory_classifies_support_given_as_affinity_and_reciprocity(self):
        evidence = ExchangeClassifier().classify({
            "id": "support-2",
            "counterparty_id": "sick-friend",
            "reason": "SICK_PARTNER_FOOD",
            "actual_received": {},
            "actual_sent": {"food": 1},
        })

        self.assertEqual(evidence.kind, "support_given")
        self.assertGreater(evidence.affinity, 0.0)
        self.assertGreater(evidence.reciprocity, 0.0)

    def test_social_memory_observes_joined_fire_as_host_generosity(self):
        memory = SocialMemory()

        memory.observe_game_state({
            "day": 3,
            "me": {
                "id": "bot-1",
                "health": "sick",
                "fire_status": "GUEST",
                "actions": [],
                "trade_history": [],
                "timeline": [
                    {"id": "fire-1", "type": "JOINED_FIRE", "data": {"host": "host-bot"}},
                ],
            },
        })

        relationship = memory.as_memory()["host-bot"]
        self.assertGreater(relationship["trust"], 0.0)
        self.assertGreater(relationship["generosity"], 0.0)
        self.assertGreater(relationship["affinity"], 0.0)

    def test_social_memory_observes_seated_guest_as_successful_support_given(self):
        memory = SocialMemory()

        memory.observe_game_state({
            "day": 3,
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "HOST",
                "actions": [],
                "trade_history": [],
                "timeline": [
                    {"id": "fire-2", "type": "SEATED_GUEST", "data": {"guest": "sick-friend"}},
                ],
            },
        })

        relationship = memory.as_memory()["sick-friend"]
        self.assertGreater(relationship["affinity"], 0.0)
        self.assertGreater(relationship["reciprocity"], 0.0)


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
            "food": 2,
            "wood": 2,
            "iron": 0,
            "fire_status": "HOST",
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

    def test_goap_legal_actions_include_contest_actions_for_enemy_developments(self):
        bot = GOAPGenetic(GOAPGenome(contest_weight=1.0, aggression_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "WORK",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 2, "wood": 2, "iron": 1},
                "actions": [],
                "available_work": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "bot-2", "health": "healthy"},
            ],
            "developments": [
                {"id": "dev-2", "type": "Farm", "level": 2, "owner_id": "bot-2", "is_contested": False},
            ],
        }

        actions = bot.get_available_actions(state)

        self.assertIn(
            {"action_command": Command.CONTEST_DEV, "payload": {"dev_id": "dev-2", "side": "INITIATOR"}},
            actions,
        )

    def test_goap_does_not_offer_another_initiation_during_an_active_contest(self):
        bot = GOAPGenetic(GOAPGenome())
        state = {
            "status": "RUNNING",
            "phase": "WORK",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 0, "wood": 0, "iron": 0},
                "actions": [],
                "available_work": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "bot-2", "health": "healthy"},
            ],
            "developments": [
                {
                    "id": "active-dev",
                    "owner_id": "bot-2",
                    "is_contested": True,
                    "contest_initiator_id": "bot-1",
                },
                {
                    "id": "stable-dev",
                    "owner_id": "bot-2",
                    "is_contested": False,
                },
            ],
            "map": [],
        }

        contest_actions = [
            action for action in bot.get_available_actions(state)
            if action["action_command"] == Command.CONTEST_DEV
        ]

        self.assertEqual(contest_actions, [{
            "action_command": Command.CONTEST_DEV,
            "payload": {"dev_id": "active-dev", "side": "CONTESTER"},
        }])

    def test_utility_bot_does_not_offer_another_initiation_during_an_active_contest(self):
        bot = GeneticBot(Genome.random())
        me = {"id": "bot-1", "health": "healthy"}
        state = {
            "map": [],
            "development_costs": {},
            "developments": [
                {
                    "id": "active-dev",
                    "owner_id": "bot-2",
                    "is_contested": True,
                    "contest_initiator_id": "bot-1",
                },
                {
                    "id": "stable-dev",
                    "owner_id": "bot-2",
                    "is_contested": False,
                },
            ],
        }
        actions = []

        bot.get_build_upgrade_maintain_contest_actions(
            state, me, {}, actions)

        self.assertNotIn({
            "action_command": "CONTEST_DEV",
            "payload": {"dev_id": "stable-dev", "side": "INITIATOR"},
        }, actions)

    def test_goap_finished_player_only_receives_work_phase_responses(self):
        bot = GOAPGenetic(GOAPGenome())
        state = {
            "status": "RUNNING",
            "phase": "WORK",
            "development_costs": {"Farm": {"build": {"food": 1}}},
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "finished_phase": True,
                "resources": {"food": 10, "wood": 10, "iron": 10},
                "actions": [],
                "available_work": [],
            },
            "player_list": [],
            "map": [{"id": "tile-1", "type": "Farm", "development": None}],
            "developments": [{
                "id": "stable-dev",
                "owner_id": "bot-2",
                "is_contested": False,
            }],
        }

        self.assertEqual(bot.get_available_actions(state), [])

    def test_utility_finished_player_is_not_offered_primary_work_actions(self):
        bot = GeneticBot(Genome.random())
        me = {
            "id": "bot-1",
            "health": "healthy",
            "finished_phase": True,
        }
        state = {
            "map": [],
            "development_costs": {},
            "developments": [{
                "id": "stable-dev",
                "owner_id": "bot-2",
                "is_contested": False,
            }],
        }
        actions = []

        bot.get_build_upgrade_maintain_contest_actions(
            state, me, {}, actions)

        self.assertEqual(actions, [])

    def test_time_pressure_policy_filters_waiting_actions_near_deadline(self):
        policy = TimePressurePolicy(deadline_fraction=0.2, minimum_deadline_seconds=1.0)
        memory = Memory({"phase": "WORK", "time_remaining": 5, "is_waiting": False})
        policy.observe(memory)
        urgent_memory = Memory({"phase": "WORK", "time_remaining": 1, "is_waiting": True})
        actions = [
            {"action_command": Command.EMPLOYMENT, "payload": {"is_application": True}},
            {"action_command": Command.COMMIT_WORK, "payload": {"job": {"wage_type": "food", "wage": 1}}},
            {"action_command": Command.CONTEST_DEV, "payload": {"dev_id": "dev-2", "side": "INITIATOR"}},
        ]

        self.assertTrue(policy.should_stop_waiting(urgent_memory))
        self.assertEqual(policy.filter_actions(actions, urgent_memory), actions[1:])

    def test_goap_stops_waiting_near_training_deadline_and_submits_immediate_work(self):
        bot = GOAPGenetic(GOAPGenome(work_weight=1.0, food_weight=1.0, food_desperation_weight=1.0))
        first_state = {
            "status": "RUNNING",
            "training": True,
            "phase": "WORK",
            "time_remaining": 5,
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 1, "wood": 2, "iron": 0},
                "actions": [{
                    "id": "application-1",
                    "type": "EMPLOYMENT",
                    "is_application": True,
                    "initiator_id": "bot-1",
                    "target_id": "bot-2",
                    "status": "PENDING",
                }],
                "available_work": [{"development": {"owner_id": "bot-1", "is_contested": False}, "wage": 2, "wage_type": "food"}],
                "finished_phase": False,
            },
            "player_list": [{"id": "bot-1", "health": "healthy"}],
            "developments": [],
        }
        late_state = {**first_state, "time_remaining": 1}

        self.assertIsNone(bot.choose_action(first_state))
        action = bot.choose_action(late_state)

        self.assertEqual(action["action_command"], Command.COMMIT_WORK)

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

    def test_resource_valuator_penalizes_spending_last_survival_resources(self):
        valuator = ResourceValuator(GOAPGenome(
            food_weight=1.0,
            wood_weight=1.0,
            food_desperation_weight=1.0,
            wood_desperation_weight=1.0,
            survival_weight=1.0,
        ))
        memory = Memory({"food": 1, "wood": 1, "iron": 0, "phase": "WORK", "fire_status": "COLD"})

        safe_gain = valuator.action_utility({"food_delta": 1.0}, memory)
        risky_spend = valuator.action_utility({"wood_cost": 1.0, "resource_cost": 1.0}, memory)

        self.assertGreater(safe_gain, 0.0)
        self.assertLess(risky_spend, -1.0)

    def test_goal_library_returns_phase_relevant_incomplete_goals(self):
        goals = GoalLibrary(GOAPGenome(
            survival_weight=1.0,
            food_desperation_weight=1.0,
            warmth_desperation_weight=1.0,
            build_weight=1.0,
            growth_weight=1.0,
        ))
        stable_work = Memory({"phase": "WORK", "food": 4, "wood": 3, "iron": 0, "fire_status": "HOST", "sickness_chance": 0.0})
        cold_night = Memory({"phase": "NIGHT", "food": 4, "wood": 0, "iron": 0, "fire_status": "COLD", "sickness_chance": 0.0})

        self.assertNotIn("SURVIVE", {goal.name for goal in goals.available_goals(stable_work)})
        self.assertIn("INCREASE_PRODUCTION", {goal.name for goal in goals.available_goals(stable_work)})
        self.assertEqual([goal.name for goal in goals.available_goals(cold_night)][0], "SECURE_WARMTH")

    def test_goal_library_prioritizes_development_loop_goals(self):
        goals = GoalLibrary(GOAPGenome(
            maintain_weight=1.0,
            upgrade_weight=1.0,
            growth_weight=1.0,
            future_reward_weight=1.0,
            work_weight=1.0,
            food_desperation_weight=1.0,
            survival_weight=1.0,
        ))
        maintenance_due = Memory({
            "phase": "WORK",
            "food": 4,
            "wood": 4,
            "iron": 2,
            "fire_status": "HOST",
            "sickness_chance": 0.0,
            "at_risk_developments": [{"id": "farm-1"}],
            "maintenance_resource_deficits": {},
            "upgradable_developments": [{"id": "farm-1"}],
            "upgrade_opportunity_value_by_resource": {"food": 8.0},
            "workable_owned_developments": [{"id": "farm-1"}],
        })
        cannot_maintain = Memory({
            **maintenance_due,
            "wood": 0,
            "maintenance_resource_deficits": {"wood": 2.0},
        })
        safe_upgrade = Memory({
            **maintenance_due,
            "at_risk_developments": [],
            "upgradable_developments": [{"id": "farm-1"}],
            "upgrade_opportunity_value_by_resource": {"food": 8.0},
        })

        self.assertIn("MAINTAIN_PRODUCTION", [goal.name for goal in goals.available_goals(maintenance_due)])
        self.assertIn("GATHER_MAINTENANCE_RESOURCES", [goal.name for goal in goals.available_goals(cannot_maintain)])
        self.assertIn("UPGRADE_PRODUCTION", [goal.name for goal in goals.available_goals(safe_upgrade)])
        self.assertIn("STAFF_PRODUCTION", [goal.name for goal in goals.available_goals(safe_upgrade)])
        starving = Memory({**safe_upgrade, "food": 0})
        self.assertGreater(goals.by_name("SURVIVE").utility(starving), goals.by_name("UPGRADE_PRODUCTION").utility(starving))

    def test_development_action_features_value_upgrade_maintenance_and_owned_work(self):
        calculator = ActionFeatureCalculator()
        memory = Memory({
            "my_id": "bot-1",
            "day": 2,
            "game_length": 6,
            "food": 3,
            "wood": 4,
            "iron": 2,
            "my_developments": [
                {
                    "id": "farm-1",
                    "type": "Farm",
                    "level": 2,
                    "owner_id": "bot-1",
                    "maintenance_days": 1,
                    "maintenance_cost": {"wood": 1},
                    "upgrade_cost": {"wood": 2, "iron": 1},
                    "can_upgrade": True,
                },
            ],
            "other_player_developments": [
                {"id": "enemy-farm", "type": "Farm", "level": 3, "owner_id": "bot-2"},
                {"id": "enemy-mine", "type": "Mine", "level": 3, "owner_id": "bot-2"},
            ],
            "available_work": [
                {"development": {"id": "farm-1", "type": "Farm", "level": 2, "owner_id": "bot-1"}, "wage": 2, "wage_type": "food"},
            ],
        })

        upgrade = calculator.calculate({"action_command": Command.UPGRADE_DEV, "payload": {"dev_id": "farm-1"}}, memory)
        maintain = calculator.calculate({"action_command": Command.MAINTAIN_DEV, "payload": {"dev_id": "farm-1"}}, memory)
        work = calculator.calculate({
            "action_command": Command.COMMIT_WORK,
            "payload": {"job": {"development": {"id": "farm-1", "type": "Farm", "level": 2, "owner_id": "bot-1"}, "wage": 2, "wage_type": "food"}},
        }, memory)
        hungry = Memory({**memory, "food": 0, "wood": 4, "iron": 4})
        contest_farm = calculator.calculate({"action_command": Command.CONTEST_DEV, "payload": {"dev_id": "enemy-farm", "side": "INITIATOR"}}, hungry)
        contest_mine = calculator.calculate({"action_command": Command.CONTEST_DEV, "payload": {"dev_id": "enemy-mine", "side": "INITIATOR"}}, hungry)

        self.assertEqual(upgrade["food_upgrade_output_delta"], 4.0)
        self.assertGreater(upgrade["upgrade_roi"], 0.0)
        self.assertGreater(maintain["maintenance_loss_avoided"], 0.0)
        self.assertGreater(maintain["food_production_protected"], 0.0)
        self.assertEqual(work["owned_work_output"], 2.0)
        self.assertEqual(work["food_production_delta"], 2.0)
        self.assertGreater(contest_farm["contested_value"], contest_mine["contested_value"])

    def test_resource_valuator_counts_future_maintenance_and_upgrade_deficits(self):
        valuator = ResourceValuator(GOAPGenome(
            wood_weight=0.1,
            iron_weight=0.1,
            maintain_weight=1.0,
            upgrade_weight=1.0,
            future_reward_weight=1.0,
        ))
        memory = Memory({
            "wood": 2,
            "iron": 0,
            "fire_status": "HOST",
            "maintenance_resource_deficits": {"iron": 1.0},
            "upgrade_resource_deficits": {"iron": 1.0},
        })

        self.assertGreater(
            valuator.action_utility({"iron_delta": 1.0}, memory),
            valuator.action_utility({"wood_delta": 1.0}, memory),
        )

    def test_actuator_scores_across_active_goals_instead_of_first_viable_goal(self):
        genome = GOAPGenome(
            survival_weight=1.0,
            food_weight=1.0,
            food_desperation_weight=1.0,
            build_weight=1.0,
            growth_weight=1.0,
            future_reward_weight=1.0,
        )
        actuator = Actuator(genome)
        memory = Memory({
            "phase": "WORK",
            "food": 4,
            "wood": 3,
            "iron": 0,
            "fire_status": "HOST",
            "sickness_chance": 0.0,
            "day": 1,
            "game_length": 12,
            "development_costs": {"Farm": {"build": {"wood": 1}}},
        })
        actions = [
            {"action_command": Command.EMPLOYMENT, "payload": {"wage_type": "food", "wage": 1}},
            {"action_command": Command.BUILD_DEV, "payload": {"tile_id": "farm", "_tile_type": "Farm"}},
        ]

        action = actuator.act("SECURE_FOOD", actions, memory)

        self.assertEqual(action["action_command"], Command.BUILD_DEV)
        self.assertEqual(actuator.last_debug_explanation["goal"], "INCREASE_PRODUCTION")

    def test_planner_subtracts_explicit_action_cost_from_score(self):
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
        planner = OneStepPlanner(GOAPGenome(
            growth_weight=1.0,
            build_weight=1.0,
            action_cost_weight=1.0,
            wood_weight=1.0,
        ))

        planned = planner.plan(goal, legal_actions, memory)

        self.assertIsNotNone(planned)
        self.assertAlmostEqual(
            planned.score,
            planned.explanation["goal_progress"]
            + planned.explanation["feature_utility"]
            + planned.explanation["resource_utility"]
            + planned.explanation["lookahead_score"]
            - planned.explanation["cost"],
        )

    def test_development_action_cost_uses_matching_maintenance_or_upgrade_cost(self):
        genome = GOAPGenome(
            maintain_weight=1.0,
            upgrade_weight=1.0,
            action_cost_weight=1.0,
            wood_weight=1.0,
            iron_weight=1.0,
        )
        planner = OneStepPlanner(genome)
        memory = Memory({
            "food": 4,
            "wood": 4,
            "iron": 2,
            "my_developments": [{
                "id": "farm-1",
                "type": "Farm",
                "level": 2,
                "owner_id": "bot-1",
                "maintenance_days": 1,
                "maintenance_cost": {"wood": 1},
                "upgrade_cost": {"wood": 2, "iron": 1},
                "can_upgrade": True,
            }],
        })

        maintain = planner.plan(
            GoalLibrary(genome).by_name("PRESERVE_ASSETS"),
            [{"action_command": Command.MAINTAIN_DEV, "payload": {"dev_id": "farm-1"}}],
            memory,
        )
        upgrade = planner.plan(
            GoalLibrary(genome).by_name("IMPROVE_ASSETS"),
            [{"action_command": Command.UPGRADE_DEV, "payload": {"dev_id": "farm-1"}}],
            memory,
        )

        self.assertIsNotNone(maintain)
        self.assertIsNotNone(upgrade)
        if maintain is None or upgrade is None:
            self.fail("expected maintain and upgrade plans")
        self.assertAlmostEqual(maintain.cost, 0.5)
        self.assertAlmostEqual(upgrade.cost, 0.75)

    def test_planner_preserves_at_risk_development_before_lower_value_growth(self):
        genome = GOAPGenome(
            maintain_weight=1.0,
            growth_weight=0.2,
            build_weight=0.2,
            future_reward_weight=1.0,
            action_cost_weight=0.0,
        )
        actuator = Actuator(genome)
        memory = Memory({
            "phase": "WORK",
            "my_id": "bot-1",
            "day": 2,
            "game_length": 8,
            "food": 4,
            "wood": 4,
            "iron": 2,
            "fire_status": "HOST",
            "sickness_chance": 0.0,
            "development_costs": {"Farm": {"build": {"wood": 1}}},
            "my_developments": [{
                "id": "farm-1",
                "type": "Farm",
                "level": 2,
                "owner_id": "bot-1",
                "maintenance_days": 1,
                "maintenance_cost": {"wood": 1},
                "upgrade_cost": {"wood": 2, "iron": 1},
                "can_upgrade": True,
            }],
            "at_risk_developments": [{"id": "farm-1"}],
            "maintenance_resource_deficits": {},
            "upgradable_developments": [{"id": "farm-1"}],
            "upgrade_resource_deficits": {},
            "upgrade_opportunity_value_by_resource": {"food": 6.0},
        })
        actions = [
            {"action_command": Command.BUILD_DEV, "payload": {"tile_id": "farm-tile", "_tile_type": "Farm"}},
            {"action_command": Command.CONTEST_DEV, "payload": {"dev_id": "enemy-farm", "side": "INITIATOR"}},
            {"action_command": Command.MAINTAIN_DEV, "payload": {"dev_id": "farm-1"}},
        ]

        action = actuator.act("INCREASE_PRODUCTION", actions, memory)

        self.assertIsNotNone(action)
        if action is None:
            self.fail("expected a maintenance action")
        self.assertEqual(action["action_command"], Command.MAINTAIN_DEV)

    def test_planner_upgrades_only_after_maintenance_is_safe(self):
        genome = GOAPGenome(
            maintain_weight=1.0,
            upgrade_weight=1.0,
            future_reward_weight=1.0,
            action_cost_weight=0.0,
        )
        actuator = Actuator(genome)
        base_memory = {
            "phase": "WORK",
            "my_id": "bot-1",
            "day": 2,
            "game_length": 8,
            "food": 4,
            "wood": 4,
            "iron": 2,
            "fire_status": "HOST",
            "sickness_chance": 0.0,
            "my_developments": [{
                "id": "farm-1",
                "type": "Farm",
                "level": 2,
                "owner_id": "bot-1",
                "maintenance_cost": {"wood": 1},
                "upgrade_cost": {"wood": 2, "iron": 1},
                "can_upgrade": True,
            }],
            "maintenance_resource_deficits": {},
            "upgradable_developments": [{"id": "farm-1"}],
            "upgrade_resource_deficits": {},
            "upgrade_opportunity_value_by_resource": {"food": 6.0},
        }
        actions = [
            {"action_command": Command.UPGRADE_DEV, "payload": {"dev_id": "farm-1"}},
            {"action_command": Command.MAINTAIN_DEV, "payload": {"dev_id": "farm-1"}},
        ]

        urgent_action = actuator.act("UPGRADE_PRODUCTION", actions, Memory({
            **base_memory,
            "my_developments": [{**base_memory["my_developments"][0], "maintenance_days": 1}],
            "at_risk_developments": [{"id": "farm-1"}],
        }))
        safe_action = actuator.act("UPGRADE_PRODUCTION", actions, Memory({
            **base_memory,
            "my_developments": [{**base_memory["my_developments"][0], "maintenance_days": 5}],
            "at_risk_developments": [],
        }))

        self.assertIsNotNone(urgent_action)
        self.assertIsNotNone(safe_action)
        if urgent_action is None or safe_action is None:
            self.fail("expected urgent and safe development actions")
        self.assertEqual(urgent_action["action_command"], Command.MAINTAIN_DEV)
        self.assertEqual(safe_action["action_command"], Command.UPGRADE_DEV)

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

    def test_action_features_score_trusted_complementary_partner_support(self):
        calculator = ActionFeatureCalculator()
        memory = Memory({
            "my_id": "bot-1",
            "relationships": {
                "trusted-miner": {
                    "trust": 0.8,
                    "fairness": 0.5,
                    "generosity": 0.2,
                    "reciprocity": 0.3,
                    "hostility": 0.0,
                    "confidence": 0.75,
                },
            },
            "trusted_partner_scores": {"trusted-miner": 1.0},
            "complementary_partner_scores": {"trusted-miner": 2.0},
            "partner_support_needs": {"trusted-miner": {"wood": 1.0}},
        })

        features = calculator.calculate({
            "action_command": Command.TRADE,
            "payload": {
                "target_id": "trusted-miner",
                "offer_items": {"wood": 1},
                "request_items": {"iron": 1},
            },
        }, memory)

        self.assertEqual(features["trusted_partner_support"], 1.0)
        self.assertEqual(features["complementary_partner_support"], 2.0)
        self.assertEqual(features["group_resource_balance_delta"], 1.0)

    def test_trade_features_score_free_food_to_sick_trusted_partner(self):
        calculator = ActionFeatureCalculator()
        memory = Memory({
            "trusted_partner_scores": {"sick-friend": 1.0},
            "partner_care_needs": {"sick-friend": {"food": 1.0}},
            "free_food_support_targets": ["sick-friend"],
        })

        features = calculator.calculate({
            "action_command": Command.TRADE,
            "payload": {
                "target_id": "sick-friend",
                "offer_items": {"food": 1},
                "request_items": {},
                "_support_reason": "SICK_PARTNER_FOOD",
            },
        }, memory)

        self.assertEqual(features["free_food_support"], 1.0)
        self.assertEqual(features["sick_partner_support"], 1.0)
        self.assertGreater(features["partner_survival_support"], 0.0)
        self.assertGreater(features["trusted_partner_support"], 0.0)

    def test_campfire_features_score_sick_partner_hosting_support(self):
        calculator = ActionFeatureCalculator()
        memory = Memory({
            "trusted_partner_scores": {"sick-friend": 1.0},
            "campfire_support_targets": ["sick-friend"],
            "partner_care_needs": {"sick-friend": {"campfire": 1.0}},
        })

        features = calculator.calculate({
            "action_command": Command.CAMPFIRE,
            "payload": {"target_id": "sick-friend", "is_request": False},
        }, memory)

        self.assertEqual(features["campfire_partner_support"], 1.0)
        self.assertEqual(features["sick_partner_support"], 1.0)
        self.assertGreater(features["partner_survival_support"], 0.0)
        self.assertGreater(features["trusted_partner_support"], 0.0)

    def test_campfire_features_do_not_score_hostile_target_as_support(self):
        calculator = ActionFeatureCalculator()
        memory = Memory({
            "trusted_partner_scores": {"hostile-player": -1.0},
            "campfire_support_targets": ["hostile-player"],
            "partner_care_needs": {"hostile-player": {"campfire": 1.0}},
        })

        features = calculator.calculate({
            "action_command": Command.CAMPFIRE,
            "payload": {"target_id": "hostile-player", "is_request": False},
        }, memory)

        self.assertNotIn("campfire_partner_support", features)
        self.assertNotIn("trusted_partner_support", features)
        self.assertEqual(features["social_exposure"], 1.0)

    def test_action_feature_scorer_rewards_group_support_with_existing_genes(self):
        scorer = ActionUtilityScorer(GOAPGenome(
            cooperation_weight=1.0,
            trust_weight=1.0,
            fairness_weight=0.5,
            reciprocity_weight=0.5,
            future_reward_weight=1.0,
            survival_weight=1.0,
        ))

        evaluation = scorer.score({
            "trusted_partner_support": 1.0,
            "complementary_partner_support": 2.0,
            "partner_survival_support": 1.0,
            "group_resource_balance_delta": 1.0,
        })

        self.assertGreater(evaluation.score, 0.0)
        self.assertGreater(evaluation.contributions["complementary_partner_support"], 0.0)

    def test_cooperate_goal_values_trusted_complementary_opportunities(self):
        goals = GoalLibrary(GOAPGenome(
            cooperation_weight=1.0,
            trust_weight=1.0,
            future_reward_weight=1.0,
            campfire_accept_weight=0.0,
        ))
        goal = goals.by_name("COOPERATE")
        trusted_memory = Memory({
            "pending_contracts": [],
            "trusted_partner_scores": {"trusted-miner": 1.0},
            "complementary_partner_scores": {"trusted-miner": 2.0},
        })
        hostile_memory = Memory({
            "pending_contracts": [],
            "trusted_partner_scores": {"hostile-miner": -1.0},
            "complementary_partner_scores": {"hostile-miner": 2.0},
        })

        self.assertGreater(goal.utility(trusted_memory), 0.0)
        self.assertEqual(goal.utility(hostile_memory), 0.0)
        self.assertGreater(goal.progress(trusted_memory, {
            "trusted_partner_support": 1.0,
            "complementary_partner_support": 1.0,
        }), 0.0)

    def test_cooperate_goal_values_sick_trusted_partner_care_need(self):
        goal = GoalLibrary(GOAPGenome(
            cooperation_weight=1.0,
            trust_weight=1.0,
            survival_weight=1.0,
        )).by_name("COOPERATE")
        memory = Memory({
            "food": 3,
            "fire_status": "HOST",
            "trusted_partner_scores": {"sick-friend": 1.0},
            "partner_care_needs": {"sick-friend": {"food": 1.0, "campfire": 1.0}},
        })

        self.assertGreater(goal.utility(memory), 0.0)
        self.assertGreater(goal.progress(memory, {
            "free_food_support": 1.0,
            "sick_partner_support": 1.0,
        }), 0.0)

    def test_cooperate_goal_does_not_value_hostile_sick_partner_care_need(self):
        goal = GoalLibrary(GOAPGenome(
            cooperation_weight=1.0,
            trust_weight=1.0,
            survival_weight=1.0,
        )).by_name("COOPERATE")
        memory = Memory({
            "food": 3,
            "fire_status": "HOST",
            "trusted_partner_scores": {"hostile-player": -1.0},
            "relationships": {"hostile-player": {"hostility": 1.0}},
            "partner_care_needs": {"hostile-player": {"food": 1.0}},
        })

        self.assertEqual(goal.utility(memory), 0.0)

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
    def test_goap_legal_actions_start_fire_when_cold_and_affordable(self):
        bot = GOAPGenetic(GOAPGenome())
        state = {
            "status": "RUNNING",
            "phase": "NIGHT",
            "campfire_cost": {"wood": 1},
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "COLD",
                "resources": {"food": 2, "wood": 1, "iron": 0},
                "actions": [],
            },
            "player_list": [{"id": "bot-1", "health": "healthy", "fire_status": "COLD"}],
        }

        actions = bot.get_available_actions(state)

        self.assertTrue(any(action["action_command"] == Command.START_FIRE for action in actions))

    def test_goap_legal_actions_request_campfire_when_cold_without_wood(self):
        bot = GOAPGenetic(GOAPGenome())
        state = {
            "status": "RUNNING",
            "phase": "NIGHT",
            "campfire_cost": {"wood": 1},
            "max_fire_seats": 2,
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "COLD",
                "resources": {"food": 2, "wood": 0, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy", "fire_status": "COLD"},
                {"id": "host", "health": "healthy", "fire_status": "HOST", "fire_guests": []},
            ],
        }

        actions = bot.get_available_actions(state)

        self.assertTrue(any(
            action["action_command"] == Command.CAMPFIRE
            and action["payload"].get("target_id") == "host"
            and action["payload"].get("is_request") is True
            for action in actions
        ))

    def test_goap_legal_actions_finalize_accepted_trade_with_feasible_items(self):
        bot = GOAPGenetic(GOAPGenome())
        state = {
            "status": "RUNNING",
            "phase": "TRADE",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 0, "wood": 1, "iron": 0},
                "actions": [{
                    "id": "trade-1",
                    "type": "TRADE",
                    "status": "ACCEPTED",
                    "initiator_id": "other",
                    "target_id": "bot-1",
                    "target_finalized": False,
                    "request_items": {"wood": 2},
                    "offer_items": {"food": 1},
                }],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "other", "health": "healthy"},
            ],
        }

        actions = bot.get_available_actions(state)
        finalize = next(action for action in actions if action["action_command"] == Command.FINALIZE)

        self.assertEqual(finalize["payload"], {
            "action_id": "trade-1",
            "actual_items": {"wood": 1},
        })

    def test_goap_legal_actions_accept_or_deny_incoming_trade(self):
        bot = GOAPGenetic(GOAPGenome())
        state = {
            "status": "RUNNING",
            "phase": "TRADE",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 1, "wood": 1, "iron": 0},
                "actions": [{
                    "id": "trade-1",
                    "type": "TRADE",
                    "status": "PENDING",
                    "waiting_on_id": "bot-1",
                    "initiator_id": "other",
                    "target_id": "bot-1",
                }],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "other", "health": "healthy"},
            ],
        }

        commands = {action["action_command"] for action in bot.get_available_actions(state)}

        self.assertIn(Command.ACCEPT, commands)
        self.assertIn(Command.DENY, commands)

    def test_goap_trade_actions_request_future_maintenance_deficits_and_keep_reserves(self):
        bot = GOAPGenetic(GOAPGenome(iron_weight=1.0, maintain_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "TRADE",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "HOST",
                "resources": {"food": 1, "wood": 4, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "other", "health": "healthy"},
            ],
        }
        memory = Memory({
            "food": 1,
            "wood": 4,
            "iron": 0,
            "fire_status": "HOST",
            "maintenance_resource_deficits": {"iron": 1.0},
            "upgrade_resource_deficits": {},
        })

        actions = bot.get_available_actions(state, memory)
        trades = [action for action in actions if action["action_command"] == Command.TRADE]

        self.assertTrue(trades)
        self.assertEqual(trades[0]["payload"]["request_items"], {"iron": 1})
        self.assertNotEqual(trades[0]["payload"]["offer_items"], {"food": 1})

    def test_goap_trade_actions_target_trusted_complementary_partner_first(self):
        bot = GOAPGenetic(GOAPGenome(iron_weight=1.0, maintain_weight=1.0, trust_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "TRADE",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "HOST",
                "resources": {"food": 2, "wood": 5, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "unknown-farmer", "health": "healthy"},
                {"id": "trusted-miner", "health": "healthy"},
            ],
        }
        memory = Memory({
            "food": 2,
            "wood": 5,
            "iron": 0,
            "fire_status": "HOST",
            "maintenance_resource_deficits": {"iron": 1.0},
            "upgrade_resource_deficits": {},
            "trusted_partner_scores": {"trusted-miner": 1.0, "unknown-farmer": 0.0},
            "complementary_partner_scores": {"trusted-miner": 3.0, "unknown-farmer": 0.1},
            "partner_specializations": {"trusted-miner": "iron", "unknown-farmer": "food"},
        })

        trades = [
            action for action in bot.get_available_actions(state, memory)
            if action["action_command"] == Command.TRADE
        ]

        self.assertTrue(trades)
        self.assertEqual(trades[0]["payload"]["target_id"], "trusted-miner")
        self.assertEqual(trades[0]["payload"]["request_items"], {"iron": 1})

    def test_goap_employment_actions_prefer_trusted_specialists_producing_needed_resources(self):
        bot = GOAPGenetic(GOAPGenome(iron_weight=1.0, trust_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "WORK",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "resources": {"food": 2, "wood": 3, "iron": 0},
                "actions": [],
                "available_work": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "unknown-farmer", "health": "healthy"},
                {"id": "trusted-miner", "health": "healthy"},
            ],
            "developments": [
                {"id": "farm-1", "type": "Farm", "level": 2, "owner_id": "unknown-farmer"},
                {"id": "mine-1", "type": "Mine", "level": 2, "owner_id": "trusted-miner"},
            ],
        }
        memory = Memory({
            "food": 2,
            "wood": 3,
            "iron": 0,
            "maintenance_resource_deficits": {"iron": 1.0},
            "upgrade_resource_deficits": {},
            "trusted_partner_scores": {"trusted-miner": 1.0, "unknown-farmer": 0.0},
            "complementary_partner_scores": {"trusted-miner": 3.0, "unknown-farmer": 0.1},
            "partner_specializations": {"trusted-miner": "iron", "unknown-farmer": "food"},
        })

        applications = [
            action for action in bot.get_available_actions(state, memory)
            if action["action_command"] == Command.EMPLOYMENT
        ]

        self.assertTrue(applications)
        self.assertEqual(applications[0]["payload"]["target_id"], "trusted-miner")
        self.assertEqual(applications[0]["payload"]["wage_type"], "iron")

    def test_goap_support_trade_offers_partner_needed_surplus_without_spending_reserves(self):
        bot = GOAPGenetic(GOAPGenome(cooperation_weight=1.0, trust_weight=1.0, iron_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "TRADE",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "HOST",
                "resources": {"food": 5, "wood": 2, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "trusted-miner", "health": "healthy"},
            ],
        }
        memory = Memory({
            "food": 5,
            "wood": 2,
            "iron": 0,
            "fire_status": "HOST",
            "maintenance_resource_deficits": {},
            "upgrade_resource_deficits": {},
            "trusted_partner_scores": {"trusted-miner": 1.0},
            "complementary_partner_scores": {"trusted-miner": 1.0},
            "partner_specializations": {"trusted-miner": "iron"},
            "partner_support_needs": {"trusted-miner": {"wood": 1.0}},
        })

        trades = [
            action for action in bot.get_available_actions(state, memory)
            if action["action_command"] == Command.TRADE
        ]

        self.assertTrue(trades)
        self.assertEqual(trades[0]["payload"]["target_id"], "trusted-miner")
        self.assertEqual(trades[0]["payload"]["offer_items"], {"wood": 1})
        self.assertEqual(trades[0]["payload"]["request_items"], {"iron": 1})

    def test_goap_trade_offers_free_food_to_trusted_sick_partner_when_safe(self):
        bot = GOAPGenetic(GOAPGenome(cooperation_weight=1.0, generosity_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "TRADE",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "HOST",
                "resources": {"food": 3, "wood": 2, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "sick-friend", "health": "sick"},
            ],
        }
        memory = Memory({
            "food": 3,
            "wood": 2,
            "iron": 0,
            "health": "healthy",
            "fire_status": "HOST",
            "free_food_support_targets": ["sick-friend"],
            "partner_care_needs": {"sick-friend": {"food": 1.0}},
            "trusted_partner_scores": {"sick-friend": 1.0},
        })

        trades = [
            action for action in bot.get_available_actions(state, memory)
            if action["action_command"] == Command.TRADE
        ]

        self.assertTrue(trades)
        self.assertEqual(trades[0]["payload"]["target_id"], "sick-friend")
        self.assertEqual(trades[0]["payload"]["offer_items"], {"food": 1})
        self.assertEqual(trades[0]["payload"]["request_items"], {})
        self.assertEqual(trades[0]["payload"]["_support_reason"], "SICK_PARTNER_FOOD")

    def test_goap_trade_does_not_offer_free_food_below_own_reserve(self):
        bot = GOAPGenetic(GOAPGenome(cooperation_weight=1.0, generosity_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "TRADE",
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "HOST",
                "resources": {"food": 1, "wood": 2, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy"},
                {"id": "sick-friend", "health": "sick"},
            ],
        }
        memory = Memory({
            "food": 1,
            "wood": 2,
            "iron": 0,
            "health": "healthy",
            "fire_status": "HOST",
            "free_food_support_targets": ["sick-friend"],
            "partner_care_needs": {"sick-friend": {"food": 1.0}},
            "trusted_partner_scores": {"sick-friend": 1.0},
        })

        trades = [
            action for action in bot.get_available_actions(state, memory)
            if action["action_command"] == Command.TRADE
        ]

        self.assertFalse(any(
            action["payload"].get("_support_reason") == "SICK_PARTNER_FOOD"
            for action in trades
        ))

    def test_goap_campfire_offers_to_trusted_sick_cold_partner_first(self):
        bot = GOAPGenetic(GOAPGenome(cooperation_weight=1.0, campfire_accept_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "NIGHT",
            "max_fire_seats": 2,
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "HOST",
                "fire_guests": [],
                "resources": {"food": 2, "wood": 1, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy", "fire_status": "HOST"},
                {"id": "healthy-neutral", "health": "healthy", "fire_status": "COLD"},
                {"id": "sick-friend", "health": "sick", "fire_status": "COLD"},
            ],
        }
        memory = Memory({
            "campfire_support_targets": ["sick-friend"],
            "trusted_partner_scores": {"sick-friend": 1.0, "healthy-neutral": 0.0},
            "complementary_partner_scores": {"sick-friend": 1.0},
        })

        offers = [
            action for action in bot.get_available_actions(state, memory)
            if action["action_command"] == Command.CAMPFIRE
            and not action["payload"].get("is_request")
        ]

        self.assertTrue(offers)
        self.assertEqual(offers[0]["payload"]["target_id"], "sick-friend")

    def test_goap_campfire_does_not_offer_when_fire_full(self):
        bot = GOAPGenetic(GOAPGenome(cooperation_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "NIGHT",
            "max_fire_seats": 1,
            "me": {
                "id": "bot-1",
                "health": "healthy",
                "fire_status": "HOST",
                "fire_guests": ["guest-1"],
                "resources": {"food": 2, "wood": 1, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "healthy", "fire_status": "HOST"},
                {"id": "sick-friend", "health": "sick", "fire_status": "COLD"},
            ],
        }
        offers = [
            action for action in bot.get_available_actions(state, Memory({"campfire_support_targets": ["sick-friend"]}))
            if action["action_command"] == Command.CAMPFIRE
            and not action["payload"].get("is_request")
        ]

        self.assertEqual(offers, [])

    def test_goap_campfire_request_prefers_trusted_host_when_sick_or_cold(self):
        bot = GOAPGenetic(GOAPGenome(trust_weight=1.0, campfire_accept_weight=1.0))
        state = {
            "status": "RUNNING",
            "phase": "NIGHT",
            "max_fire_seats": 2,
            "me": {
                "id": "bot-1",
                "health": "sick",
                "fire_status": "COLD",
                "fire_guests": [],
                "resources": {"food": 1, "wood": 0, "iron": 0},
                "actions": [],
            },
            "player_list": [
                {"id": "bot-1", "health": "sick", "fire_status": "COLD"},
                {"id": "unknown-host", "health": "healthy", "fire_status": "HOST", "fire_guests": []},
                {"id": "trusted-host", "health": "healthy", "fire_status": "HOST", "fire_guests": []},
            ],
        }
        memory = Memory({"trusted_partner_scores": {"trusted-host": 1.0, "unknown-host": 0.0}})

        requests = [
            action for action in bot.get_available_actions(state, memory)
            if action["action_command"] == Command.CAMPFIRE
            and action["payload"].get("is_request")
        ]

        self.assertTrue(requests)
        self.assertEqual(requests[0]["payload"]["target_id"], "trusted-host")

    def test_goap_survival_fields_are_declared_and_trainable(self):
        self.assertTrue(GOAPGenome.survival_field_names().issubset(GOAPGenome.field_names()))
        self.assertEqual(GOAPGenome.recommended_training_field_names(), GOAPGenome.field_names())

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
        self.assertEqual(genome.food_weight, 0.0)

    def test_bot_server_seeds_goap_population_with_goap_genomes(self):
        genomes = seed_genomes_for_model("GOAPGenetic", None, 3)

        self.assertEqual(len(genomes), 3)
        self.assertTrue(all(isinstance(genome, GOAPGenome) for genome in genomes))


if __name__ == "__main__":
    unittest.main()
