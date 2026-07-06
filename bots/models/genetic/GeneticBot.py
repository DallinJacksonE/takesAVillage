from BaseBot import BaseBot
from models.genetic.Genome import Genome
'''from Relationship import Relationship'''
import copy


class GeneticBot(BaseBot):
    def __init__(self, genome):
        self.genome = genome
        self.type_to_resource = {"woods": "wood", "farm": "food", "mine": "iron"}
        self.relationships = {}
        super().__init__()

    @staticmethod
    def from_json(genome_json):
        return GeneticBot(Genome(**genome_json))
    
    '''def initialize_relationships(self, state):
        me = state.get("me", {})
        for player in state.get("player_list", []):
            player_id = player.get("id")
            if player_id == me.get("id"):
                continue
            if player_id not in self.relationships:
                self.relationships[player_id] = Relationship(
                    trust=self.genome.initial_trust,
                    friendship=self.genome.initial_friendship,
                    generosity=self.genome.initial_generosity,
                    greed=self.genome.initial_greed
                )
    
    def relationship(self, player_id):
        return self.relationships[player_id]
    
    def update_relationship(
        self,
        player_id,
        *,
        trust=0,
        friendship=0,
        generosity=0,
        greed=0
    ):
        r = self.relationships[player_id]

        r.trust = max(-1, min(1, r.trust + trust))
        r.friendship = max(-1, min(1, r.friendship + friendship))
        r.generosity = max(-1, min(1, r.generosity + generosity))
        r.greed = max(-1, min(1, r.greed + greed))

    def process_finished_action(self, action, old_state, new_state):

        if action["type"] != "TRADE":
            return

        me = old_state["me"]

        other_id = (
            action["receiver_id"]
            if action["initiator_id"] == me["id"]
            else action["initiator_id"]
        )

        self.update_relationship(
            other_id,
            trust=0.10,
            friendship=0.02
        )

    def process_relationship_events(self, old_state, new_state):
        old_actions = {
            a["id"]: a
            for a in old_state["me"].get("actions", [])
        }

        new_actions = {
            a["id"]: a
            for a in new_state["me"].get("actions", [])
        }

        for action_id, action in old_actions.items():

            if action_id in new_actions:
                continue

            self.process_finished_action(action, old_state, new_state)'''

    def adjusted_resource_value(self, bundle, me):
        resources = me.get("resources", {})

        food_need = max(0, 5 - resources.get("food", 0))
        wood_need = max(0, 5 - resources.get("wood", 0))
        iron_need = max(0, 5 - resources.get("iron", 0))

        g = self.genome

        return (
            bundle.get("food", 0)
            * (g.food_weight + food_need * g.food_desperation_weight)
            +
            bundle.get("wood", 0)
            * (g.wood_weight + wood_need * g.wood_desperation_weight)
            +
            bundle.get("iron", 0)
            * (g.iron_weight + iron_need * g.iron_desperation_weight)
        )
    
    def resource_value(self,bundle):
        return (
            bundle.get("food", 0) * self.genome.food_weight +
            bundle.get("wood", 0) * self.genome.wood_weight +
            bundle.get("iron", 0) * self.genome.iron_weight
        )

    def choose_action(self, game_state: dict) -> dict | None:
        """
        Evaluates actions using genetic weights and returns a
        formatted payload.
        """
        me = game_state.get("me", {})

        if game_state.get("status") == "WAITING":
            return None

        actions = self.get_available_actions(game_state)

        if me.get("health") == "dead":
            return None
        
        '''if self.previous_state is not None:
            self.process_relationship_events(
                self.previous_state,
                game_state
            )

        self.previous_state = copy.deepcopy(game_state)

        self.initialize_relationships(game_state)'''

        if  game_state.get("phase") == "NIGHT":
            accept_actions = [
                a for a in actions
                if a["action_command"] == "ACCEPT"
            ]
            if accept_actions:
                return self.format_network_payload(accept_actions[0])
        elif game_state.get("phase") == "WORK":

            response_actions = [
                a for a in actions
                if a["action_command"] in ("ACCEPT", "DENY")
            ]

            if response_actions:
                best = max(
                    response_actions,
                    key=lambda a: self.score_action(a, game_state)
                )
                return self.format_network_payload(best)

        elif game_state.get("phase") == "TRADE":

            finalize_action = next(
                (
                    a for a in actions
                    if a["action_command"] == "FINALIZE"
                ),
                None
            )

            if finalize_action:
                return self.format_network_payload(finalize_action)

            trade_responses = [
                a for a in actions
                if a["action_command"] in ["ACCEPT", "DENY"]
            ]

            if trade_responses:
                best_response = max(
                    trade_responses,
                    key=lambda a: self.score_action(a, game_state)
                )

                return self.format_network_payload(best_response)

        if me.get("finished_phase"):
            return None

        print(f"available actions for bot: {actions}")

        if self.waiting:
            return None
        
        # 2. If no valid moves, finish the phase
        if not actions:
            return self.format_network_payload(None)

        # 3. Score and select the best action
        best_action = max(
            actions,
            key=lambda a: self.score_action(a, game_state)
        )

        # 4. Use the base class to clean and format the DTO
        return self.format_network_payload(best_action)

    def score_action(self, action: dict, game_state: dict) -> float:
        """Scores an action dict using the bot's genome."""
        g = self.genome
        score = 0
        command = action["action_command"]
        contract = None
        me = game_state.get("me", {})

        if "action_id" in action.get("payload", {}):
            action_id = action["payload"]["action_id"]

            contract = next(
                (
                    a for a in me.get("actions", [])
                    if a.get("id") == action_id
                ),
                None
            )

        contract_type = contract.get("type") if contract else None
            
        resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})

        food = resources.get("food", 0)
        wood = resources.get("wood", 0)
        iron = resources.get("iron", 0)

        # =====================
        # NEEDS
        # =====================
        food_need = max(0, 5 - food)
        wood_need = max(0, 5 - wood)
        iron_need = max(0, 5 - iron)

        if command == "EMPLOYMENT":
            score += g.work_weight

            wage = action["payload"].get("wage", 0)
            wage_type = action["payload"].get("wage_type")

            if wage_type == "food":
                score += (wage * g.food_weight)
                score += (food_need * g.food_desperation_weight)
            elif wage_type == "wood":
                score += (wage * g.wood_weight)
                score += (wood_need * g.wood_desperation_weight)
            elif wage_type == "iron":
                score += (wage * g.iron_weight)
                score += (iron_need * g.iron_desperation_weight)

            score -= .25 # prefer working for self all else equal

        # =====================
        # BUILD
        # =====================
        elif command == "BUILD_DEV":
            score += g.build_weight

            # Retrieve the injected hidden type from BaseBot
            tile_type = action["payload"].get("_tile_type")

            if tile_type == "Farm":
                score += (g.farm_preference + g.growth_weight)
                if food_need > 0:
                    score += (food_need * g.survival_weight)
            elif tile_type == "Woods":
                score += (g.woods_preference + g.growth_weight)
            elif tile_type == "Mine":
                score += (g.mine_preference + g.growth_weight)

        # =====================
        # UPGRADE / MAINTAIN / CONTEST
        # =====================
        elif command == "UPGRADE_DEV":
            score += (g.upgrade_weight + g.growth_weight)

            dev_id = action["payload"]["dev_id"]

            dev = next(
                (
                    d for d in game_state.get("developments", [])
                    if d["id"] == dev_id
                ),
                None
            )

            if dev:
                
                dev_type = dev.get("type")

                if dev_type == "Farm":
                    score += g.farm_preference
                elif dev_type == "Woods":
                    score += g.woods_preference
                elif dev_type == "Mine":
                    score += g.mine_preference

                level = dev.get("level", 1)
                days_left = dev.get("maintenance_days")

                # Growth value
                score += level * g.future_reward_weight

                urgency_bonus = max(0, 5 - days_left)

                score += (
                    urgency_bonus
                    * (g.maintain_weight
                    + g.upgrade_weight)
                    )

        elif command == "MAINTAIN_DEV":
            score += (g.maintain_weight + g.future_reward_weight)

            dev_id = action["payload"]["dev_id"]

            dev = next(
                (
                    d for d in game_state.get("developments", [])
                    if d["id"] == dev_id
                ),
                None
            )

            if dev:
                days_left = dev.get("maintenance_days")
                score += (
                    max(0, 5 - days_left)
                    * g.maintain_weight
                )

        elif command == "CONTEST_DEV":

            side = action["payload"].get("side")
            dev_id = action["payload"].get("dev_id")

            dev = next(
                (d for d in game_state.get("developments", [])
                if d["id"] == dev_id),
                None
            )

            if dev:
                score += dev.get("level", 1) * g.future_reward_weight

                if side == "OWNER":

                    if dev["owner_id"] == me["id"]:
                        score += (
                            dev["level"]
                            * g.future_reward_weight
                            * 3
                        )

                    score += g.cooperation_weight

                elif side == "INITIATOR":
                    score += (
                        g.contest_weight +
                        g.aggression_weight
                    )

                elif side == "CONTESTER":
                    score += (
                        g.contest_weight +
                        g.cooperation_weight
                    )

        # =====================
        # CAMPFIRE
        # =====================
        elif command == "START_FIRE":
            score += (g.fire_weight + g.cooperation_weight +
                      g.reputation_weight)

        # =====================
        # WORK
        # =====================
        elif command == "COMMIT_WORK":
            score += g.work_weight
            job = action["payload"]["job"]
            wage = job.get("wage", 0)
            wage_type = job.get("wage_type")

            if wage_type == "food":
                score += (wage * g.food_weight)
                score += (food_need * g.food_desperation_weight)
            elif wage_type == "wood":
                score += (wage * g.wood_weight)
                score += (wood_need * g.wood_desperation_weight)
            elif wage_type == "iron":
                score += (wage * g.iron_weight)
                score += (iron_need * g.iron_desperation_weight)

        
        if contract:

            if contract_type == "EMPLOYMENT":

                dev = next(
                    (
                        d for d in game_state.get("developments", [])
                        if d["id"] == contract.get("dev_id")
                    ),
                    None
                )

                if not dev:
                    return -9999

                produced_resource = self.type_to_resource[dev["type"].lower()]
                produced_amount = dev["level"]

                produced_value = self.adjusted_resource_value(
                    {produced_resource: produced_amount},
                    me
                )

                wage_value = self.adjusted_resource_value(
                    {contract["wage_type"]: contract["wage"]},
                    me
                )

                net_value = produced_value - wage_value
                
                # checks to only accept affordable trades
                future_food = food
                future_wood = wood
                future_iron = iron

                if produced_resource == "food":
                    future_food += produced_amount
                elif produced_resource == "wood":
                    future_wood += produced_amount
                elif produced_resource == "iron":
                    future_iron += produced_amount
                
                can_afford = (
                    (contract["wage_type"] == "food" and future_food >= contract["wage"])
                    or
                    (contract["wage_type"] == "wood" and future_wood >= contract["wage"])
                    or
                    (contract["wage_type"] == "iron" and future_iron >= contract["wage"])
                )
                
                if not can_afford:
                    if command == "ACCEPT":
                        return -100000
                    else:  # DENY
                        return 100000
                    
                # symmetric decision scoring
                if command == "ACCEPT":
                    score += net_value + 0.01
                elif command == "DENY":
                    score -= net_value

            elif contract_type == "TRADE":

                if contract["initiator_id"] == me["id"]:
                    given = contract.get("offer_items", {})
                    received = contract.get("request_items", {})
                    '''r = self.relationships[contract["target_id"]]'''
                else:
                    given = contract.get("request_items", {})
                    received = contract.get("offer_items", {})
                    '''r = self.relationships[contract["initiator_id"]]'''

                can_fulfill = all(
                    resources.get(r, 0) >= qty
                    for r, qty in given.items()
                )
                
                if not can_fulfill:
                    if command == "ACCEPT":
                        return -100000
                    elif command == "DENY":
                        return 100000

                utility = (
                    self.adjusted_resource_value(received, me) - self.adjusted_resource_value(given, me))
                '''+r.trust * g.trust_weight
                    +r.friendship * g.friendship_weight
                    -r.greed * g.greed_weight
                    +r.generosity * g.generosity_weight'''

                if command == "ACCEPT":
                    score += utility + g.cooperation_weight
                elif command == "DENY":
                    score -= utility

        if command == "FINALIZE":
            # Prefer to finalize (ship goods) if we can actually send the items
            actual = action.get("payload", {}).get("actual_items", {})
            feasible = {
                r: min(int(qty), resources.get(r, 0))
                for r, qty in actual.items()
            }
            feasible_value = self.resource_value(feasible)

            if feasible_value > 0:
                # Strongly favor finalizing when we can ship what we promised
                score += 15000
                score += feasible_value * 50
            else:
                # If we can't ship anything, deprioritize
                score -= 1000
        # =====================
        # RANDOMNESS
        # =====================
        score += (g.risk_weight * 0.1)

        return score
